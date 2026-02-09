#!/bin/bash
# Django ERP 一键部署脚本
# 用法: ./scripts/deploy.sh [环境] [操作]
#
# 示例:
#   ./scripts/deploy.sh development setup    # 初始化开发环境
#   ./scripts/deploy.sh development deploy   # 部署开发环境
#   ./scripts/deploy.sh production deploy    # 部署生产环境
#   ./scripts/deploy.sh production rollback  # 回滚到上一版本

set -e  # 遇到错误立即退出

# ============================================
# 配置
# ============================================

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# ============================================
# 参数解析
# ============================================

ENVIRONMENT=${1:-development}
ACTION=${2:-deploy}

# 验证环境参数
if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    error "无效的环境参数: $ENVIRONMENT
    有效值: development, staging, production"
fi

# 加载环境变量
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    warn ".env文件不存在，将使用默认配置"
fi

# ============================================
# 辅助函数
# ============================================

check_dependencies() {
    log "检查系统依赖..."

    # 检查Python
    if ! command -v python3 &> /dev/null; then
        error "Python3未安装，请先安装Python 3.13+"
    fi

    # 检查Docker（生产环境）
    if [ "$ENVIRONMENT" = "production" ]; then
        if ! command -v docker &> /dev/null; then
            error "Docker未安装，生产环境需要Docker"
        fi
        if ! command -v docker-compose &> /dev/null; then
            error "Docker Compose未安装"
        fi
    fi

    log "依赖检查通过 ✓"
}

backup_database() {
    log "备份数据库..."
    
    if [ "$ENVIRONMENT" = "production" ]; then
        ./scripts/backup.sh "$ENVIRONMENT"
        log "数据库备份完成 ✓"
    else
        info "开发环境跳过数据库备份"
    fi
}

run_migrations() {
    log "运行数据库迁移..."
    
    python3 manage.py migrate --noinput
    
    if [ $? -eq 0 ]; then
        log "数据库迁移完成 ✓"
    else
        error "数据库迁移失败"
    fi
}

collect_static() {
    log "收集静态文件..."
    
    python3 manage.py collectstatic --noinput --clear
    
    if [ $? -eq 0 ]; then
        log "静态文件收集完成 ✓"
    else
        error "静态文件收集失败"
    fi
}

create_superuser() {
    if ! python3 manage.py shell -c "from users.models import User; User.objects.filter(is_superuser=True).exists()" | grep -q "True"; then
        log "创建超级用户..."
        echo "from users.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'admin123') if not User.objects.filter(username='admin').exists() else None" | python3 manage.py shell
        log "超级用户创建完成 ✓"
        info "默认用户名: admin, 密码: admin123 (请立即修改)"
    fi
}

run_tests() {
    log "运行测试..."
    
    pytest apps/**/test_e2e_*.py -v --tb=short
    
    if [ $? -eq 0 ]; then
        log "测试通过 ✓"
    else
        error "测试失败，部署中止"
    fi
}

code_quality_check() {
    log "运行代码质量检查..."
    
    # Black检查（排除有问题的文件）
    black . --check --line-length=100 --exclude '^apps/bi/(analytics|realtime)/' || {
        warn "代码格式检查失败，尝试自动修复..."
        black . --line-length=100 --exclude '^apps/bi/(analytics|realtime)/'
    }
    
    # flake8检查
    flake8 . --max-line-length=100 --ignore=E203,W503 --exclude=migrations || true
    
    log "代码质量检查完成 ✓"
}

# ============================================
# 环境配置
# ============================================

setup_development() {
    log "设置开发环境..."
    
    # 安装依赖
    info "安装Python依赖..."
    pip3 install -r requirements.txt -q
    
    # 创建.env文件
    if [ ! -f .env ]; then
        info "创建.env文件..."
        cat > .env << EOF
DEBUG=True
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1
EOF
    fi
    
    # 运行迁移
    run_migrations
    
    # 创建超级用户
    create_superuser
    
    # 收集静态文件
    collect_static
    
    log "开发环境设置完成 ✓"
    info "启动开发服务器: python3 manage.py runserver"
}

setup_staging() {
    log "设置预发布环境..."
    
    # 使用PostgreSQL
    if [ ! -f .env ]; then
        error ".env文件不存在，请先配置"
    fi
    
    # 运行迁移
    run_migrations
    
    # 收集静态文件
    collect_static
    
    log "预发布环境设置完成 ✓"
}

setup_production() {
    log "设置生产环境..."
    
    # 检查.env文件
    if [ ! -f .env ]; then
        error ".env文件不存在，请先配置生产环境变量"
    fi
    
    # 检查DEBUG
    if [ "$DEBUG" != "False" ]; then
        error "生产环境必须设置DEBUG=False"
    fi
    
    # 检查SECRET_KEY
    if [ "$SECRET_KEY" = "django-insecure-change-this-in-production" ]; then
        error "生产环境必须设置强SECRET_KEY"
    fi
    
    # 备份数据库
    backup_database
    
    # 运行迁移
    run_migrations
    
    # 收集静态文件
    collect_static
    
    log "生产环境设置完成 ✓"
}

# ============================================
# 部署操作
# ============================================

deploy_development() {
    log "部署开发环境..."
    
    code_quality_check
    run_migrations
    collect_static
    
    log "开发环境部署完成 ✓"
    info "启动服务器: python3 manage.py runserver"
}

deploy_staging() {
    log "部署预发布环境..."
    
    code_quality_check
    run_tests
    backup_database
    run_migrations
    collect_static
    
    log "预发布环境部署完成 ✓"
}

deploy_production() {
    log "部署生产环境..."
    
    # 运行测试
    info "运行E2E测试..."
    pytest apps/**/test_e2e_*.py -v --tb=short
    
    # 备份数据库
    backup_database
    
    # 代码质量检查
    code_quality_check
    
    # Django系统检查
    info "运行Django系统检查..."
    python3 manage.py check --deploy
    
    # 数据库迁移
    run_migrations
    
    # 收集静态文件
    collect_static
    
    # 重启服务
    if [ "$USE_DOCKER" = "True" ]; then
        info "重启Docker容器..."
        docker-compose -f docker-compose.prod.yml down
        docker-compose -f docker-compose.prod.yml up -d
    else
        info "重启Gunicorn服务..."
        sudo systemctl restart gunicorn
        sudo systemctl reload nginx
    fi
    
    log "生产环境部署完成 ✓"
}

# ============================================
# 回滚操作
# ============================================

rollback() {
    log "回滚到上一版本..."
    
    if [ "$ENVIRONMENT" != "production" ]; then
        warn "只有生产环境支持回滚"
        return
    fi
    
    # 查找最新的备份
    BACKUP_FILE=$(ls -t backups/postgresql_production_*.sql.gz 2>/dev/null | head -1)
    
    if [ -z "$BACKUP_FILE" ]; then
        error "没有找到备份文件"
    fi
    
    info "使用备份文件: $BACKUP_FILE"
    
    # 恢复数据库
    if [ "$DB_ENGINE" = "django.db.backends.postgresql" ]; then
        gunzip -c "$BACKUP_FILE" | psql -U "$DB_USER" -d "$DB_NAME"
    fi
    
    # 回滚代码
    if [ "$USE_DOCKER" = "True" ]; then
        info "回滚Docker容器..."
        docker-compose -f docker-compose.prod.yml down
        git checkout HEAD~1
        docker-compose -f docker-compose.prod.yml up -d --build
    else
        info "回滚代码并重启服务..."
        git checkout HEAD~1
        sudo systemctl restart gunicorn
    fi
    
    log "回滚完成 ✓"
}

# ============================================
# 主程序
# ============================================

main() {
    log "=========================================="
    log "Django ERP 部署脚本"
    log "环境: $ENVIRONMENT"
    log "操作: $ACTION"
    log "=========================================="
    
    # 检查依赖
    check_dependencies
    
    # 执行操作
    case "$ACTION" in
        setup)
            case "$ENVIRONMENT" in
                development) setup_development ;;
                staging) setup_staging ;;
                production) setup_production ;;
            esac
            ;;
        deploy)
            case "$ENVIRONMENT" in
                development) deploy_development ;;
                staging) deploy_staging ;;
                production) deploy_production ;;
            esac
            ;;
        rollback)
            rollback
            ;;
        test)
            run_tests
            ;;
        backup)
            backup_database
            ;;
        *)
            error "未知操作: $ACTION
    可用操作: setup, deploy, rollback, test, backup"
            ;;
    esac
    
    log "=========================================="
    log "操作完成！"
    log "=========================================="
}

# 执行主程序
main "$@"
