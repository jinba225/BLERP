#!/bin/bash
# Django ERP 一键启动脚本
# 用法: ./scripts/start.sh [环境]
#
# 示例:
#   ./scripts/start.sh development   # 启动开发环境
#   ./scripts/start.sh production    # 启动生产环境

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 参数解析
ENVIRONMENT=${1:-development}

log "=========================================="
log "Django ERP 一键启动脚本"
log "环境: $ENVIRONMENT"
log "=========================================="
echo ""

# 加载环境变量
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    warn ".env文件不存在，使用默认配置"
fi

# ============================================
# 1. 系统检查
# ============================================
log "1. 系统检查..."

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3未安装"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
log "   ✓ Python版本: $PYTHON_VERSION"

# 检查依赖
if ! python3 -c "import django" &> /dev/null; then
    log "   安装依赖..."
    pip3 install -r requirements.txt -q
fi

log "   ✓ 系统检查完成"
echo ""

# ============================================
# 2. 数据库检查
# ============================================
log "2. 数据库检查..."

if [ "$ENVIRONMENT" = "development" ]; then
    # SQLite检查
    if [ ! -f db.sqlite3 ]; then
        log "   创建数据库..."
        python3 manage.py migrate --noinput
    fi
    log "   ✓ 数据库就绪"
else
    # PostgreSQL检查
    if ! PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1" &> /dev/null; then
        warn "   数据库连接失败，请检查配置"
    else
        log "   ✓ 数据库连接正常"
    fi
fi
echo ""

# ============================================
# 3. 迁移检查
# ============================================
log "3. 数据库迁移..."

MIGRATIONS=$(python3 manage.py showmigrations | grep "\[ \]" | wc -l)
if [ "$MIGRATIONS" -gt 0 ]; then
    log "   应用新迁移..."
    python3 manage.py migrate --noinput
else
    log "   ✓ 所有迁移已应用"
fi
echo ""

# ============================================
# 4. 静态文件
# ============================================
log "4. 静态文件..."

if [ ! -d "staticfiles" ] || [ -z "$(ls -A staticfiles)" ]; then
    log "   收集静态文件..."
    python3 manage.py collectstatic --noinput
else
    log "   ✓ 静态文件已收集"
fi
echo ""

# ============================================
# 5. 创建超级用户（开发环境）
# ============================================
if [ "$ENVIRONMENT" = "development" ]; then
    log "5. 管理员账户..."

    if ! python3 manage.py shell -c "from users.models import User; User.objects.filter(is_superuser=True).exists()" 2>/dev/null | grep -q "True"; then
        warn "   提示: 未检测到超级用户"
        echo "   创建命令: python manage.py createsuperuser"
    else
        log "   ✓ 管理员账户存在"
    fi
    echo ""
fi

# ============================================
# 6. 启动服务
# ============================================
log "6. 启动服务..."

if [ "$ENVIRONMENT" = "production" ]; then
    log "   生产环境启动..."
    
    # 使用Docker Compose
    if command -v docker-compose &> /dev/null; then
        docker-compose -f docker-compose.prod.yml up -d
        log "   ✓ Docker容器已启动"
        log ""
        log "   查看日志: docker-compose -f docker-compose.prod.yml logs -f"
        log "   停止服务: docker-compose -f docker-compose.prod.yml down"
    elif command -v gunicorn &> /dev/null; then
        log "   启动Gunicorn..."
        gunicorn django_erp.wsgi:application \
            --bind 0.0.0.0:8000 \
            --workers 3 \
            --access-logfile - \
            --error-logfile -
    else
        warn "   未找到Docker或Gunicorn，使用开发服务器"
        python3 manage.py runserver 0.0.0.0:8000
    fi
else
    log "   开发环境启动..."
    log "   启动Django开发服务器..."
    log ""
    log "   🚀 服务器地址: http://localhost:8000"
    log "   📚 管理后台: http://localhost:8000/admin/"
    log "   📖 API文档: http://localhost:8000/api/schema/"
    log ""
    log "   按 Ctrl+C 停止服务器"
    echo ""
    
    python3 manage.py runserver 0.0.0.0:8000
fi
