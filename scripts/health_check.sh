#!/bin/bash
# Django ERP 系统健康检查脚本
# 用法: ./scripts/health_check.sh

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 检查结果
FAILS=0
PASSES=0

# 检查函数
check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSES++))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAILS++))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

echo "=========================================="
echo "Django ERP 系统健康检查"
echo "=========================================="
echo ""

# ============================================
# 1. 环境检查
# ============================================
echo "📋 环境检查..."

# Python版本
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 13 ]; then
    check_pass "Python版本: $PYTHON_VERSION"
else
    check_fail "Python版本过低: $PYTHON_VERSION (需要 >= 3.13)"
fi

# Django检查
if python3 -c "import django; print(django.get_version())" &> /dev/null; then
    DJANGO_VERSION=$(python3 -c "import django; print(django.get_version())")
    check_pass "Django版本: $DJANGO_VERSION"
else
    check_fail "Django未安装"
fi

# 检查环境变量文件
if [ -f .env ]; then
    check_pass ".env文件存在"

    # 检查DEBUG模式
    if grep -q "DEBUG=False" .env; then
        check_pass "生产环境配置: DEBUG=False"
    elif grep -q "DEBUG=True" .env; then
        check_warn "开发环境配置: DEBUG=True"
    else
        check_fail "DEBUG未配置"
    fi

    # 检查SECRET_KEY
    if grep -q "SECRET_KEY=django-insecure" .env; then
        check_fail "使用默认SECRET_KEY（不安全）"
    else
        check_pass "SECRET_KEY已配置"
    fi
else
    check_fail ".env文件不存在"
fi

echo ""

# ============================================
# 2. 数据库检查
# ============================================
echo "💾 数据库检查..."

# 数据库文件检查（SQLite）
if [ -f db.sqlite3 ]; then
    DB_SIZE=$(du -h db.sqlite3 | cut -f1)
    check_pass "SQLite数据库存在: $DB_SIZE"

    # 检查数据库权限
    if [ -r db.sqlite3 ] && [ -w db.sqlite3 ]; then
        check_pass "数据库权限正常"
    else
        check_fail "数据库权限异常"
    fi
else
    # PostgreSQL检查
    if grep -q "postgresql" .env 2>/dev/null; then
        if command -v psql &> /dev/null; then
            check_pass "PostgreSQL客户端已安装"
        else
            check_warn "PostgreSQL客户端未安装"
        fi
    fi
fi

# 运行数据库检查
if python3 manage.py check --database default &> /dev/null; then
    check_pass "数据库连接正常"
else
    check_fail "数据库连接失败"
fi

echo ""

# ============================================
# 3. 应用检查
# ============================================
echo "🚀 应用检查..."

# Django系统检查
if python3 manage.py check &> /dev/null; then
    check_pass "Django系统检查通过"
else
    ISSUES=$(python3 manage.py check 2>&1 | grep "?:")
    check_fail "Django系统检查发现问题:\n$ISSUES"
fi

# 迁移检查
MIGRATIONS=$(python3 manage.py showmigrations | grep -c "\[ \]" || true)
if [ "$MIGRATIONS" -eq 0 ]; then
    check_pass "所有迁移已应用"
else
    check_warn "有 $MIGRATIONS 个未应用的迁移"
fi

# 静态文件检查
if [ -d "staticfiles" ]; then
    STATIC_FILES=$(find staticfiles -type f | wc -l)
    check_pass "静态文件已收集: $STATIC_FILES 个文件"
else
    check_warn "静态文件未收集"
fi

# 日志目录检查
if [ -d "logs" ]; then
    check_pass "日志目录存在"
else
    check_warn "日志目录不存在（将在首次运行时创建）"
fi

echo ""

# ============================================
# 4. 依赖检查
# ============================================
echo "📦 依赖检查..."

# 检查关键依赖
DEPENDENCIES=(
    "djangorestframework"
    "django_filters"
    "celery"
    "redis"
    "pytest"
)

for dep in "${DEPENDENCIES[@]}"; do
    if python3 -c "import $dep" &> /dev/null; then
        check_pass "$dep 已安装"
    else
        check_fail "$dep 未安装"
    fi
done

echo ""

# ============================================
# 5. 性能检查
# ============================================
echo "⚡ 性能检查..."

# Redis检查（如果配置）
if grep -q "REDIS_HOST=" .env 2>/dev/null; then
    REDIS_HOST=$(grep "REDIS_HOST=" .env | cut -d'=' -f2)
    if [ -n "$REDIS_HOST" ] && [ "$REDIS_HOST" != "None" ]; then
        if command -v redis-cli &> /dev/null; then
            if redis-cli -h "$REDIS_HOST" ping &> /dev/null; then
                check_pass "Redis连接正常"
            else
                check_fail "Redis连接失败"
            fi
        else
            check_warn "redis-cli未安装，跳过Redis检查"
        fi
    fi
fi

# Celery检查（可选）
if pgrep -f "celery" > /dev/null; then
    check_pass "Celery worker运行中"
else
    check_warn "Celery worker未运行"
fi

echo ""

# ============================================
# 6. 安全检查
# ============================================
echo "🔒 安全检查..."

# 部署模式检查
DEPLOY_CHECK=$(python3 manage.py check --deploy 2>&1 || true)
if [ -z "$DEPLOY_CHECK" ]; then
    check_pass "部署安全检查通过"
else
    # 过滤已知警告
    WARNINGS=$(echo "$DEPLOY_CHECK" | grep -v "You have not set a value" || true)
    if [ -z "$WARNINGS" ]; then
        check_pass "部署安全检查通过（有已知警告）"
    else
        check_warn "部署检查发现问题:\n$WARNINGS"
    fi
fi

# HTTPS检查（生产环境）
if grep -q "DEBUG=False" .env 2>/dev/null; then
    if grep -q "SECURE_SSL_REDIRECT=True" .env 2>/dev/null || \
       grep -q "SECURE_SSL_REDIRECT = True" django_erp/settings.py; then
        check_pass "HTTPS重定向已启用"
    else
        check_fail "HTTPS重定向未启用（生产环境必须）"
    fi
fi

# HSTS检查
if grep -q "SECURE_HSTS_SECONDS" django_erp/settings.py; then
    check_pass "HSTS已配置"
else
    check_warn "HSTS未配置"
fi

echo ""

# ============================================
# 7. 测试检查
# ============================================
echo "🧪 测试检查..."

# 检查E2E测试
if [ -d "apps" ]; then
    E2E_TESTS=$(find apps -name "test_e2e_*.py" | wc -l)
    if [ "$E2E_TESTS" -gt 0 ]; then
        check_pass "E2E测试文件: $E2E_TESTS 个"
    else
        check_warn "未找到E2E测试文件"
    fi
fi

echo ""

# ============================================
# 8. 备份检查
# ============================================
echo "💼 备份检查..."

if [ -d "backups" ]; then
    BACKUP_COUNT=$(find backups -name "*.sql.gz" -o -name "*.sqlite3.gz" | wc -l)
    if [ "$BACKUP_COUNT" -gt 0 ]; then
        LATEST_BACKUP=$(ls -t backups/*.sql.gz backups/*.sqlite3.gz 2>/dev/null | head -1)
        BACKUP_AGE=$(find "$LATEST_BACKUP" -mtime +1 2>/dev/null && echo "old" || echo "recent")

        if [ "$BACKUP_AGE" = "recent" ]; then
            check_pass "备份存在: $BACKUP_COUNT 个文件（最新备份24小时内）"
        else
            check_warn "备份存在: $BACKUP_COUNT 个文件（最新备份超过24小时）"
        fi
    else
        check_warn "备份目录为空"
    fi
else
    check_warn "备份目录不存在"
fi

echo ""

# ============================================
# 9. 监控检查
# ============================================
echo "📊 监控检查..."

# Sentry检查
if grep -q "SENTRY_DSN=" .env 2>/dev/null; then
    SENTRY_DSN=$(grep "SENTRY_DSN=" .env | cut -d'=' -f2)
    if [ -n "$SENTRY_DSN" ] && [ "$SENTRY_DSN" != "None" ] && [ "$SENTRY_DSN" != "''" ]; then
        check_pass "Sentry已配置"
    else
        check_warn "Sentry未配置"
    fi
else
    check_warn "Sentry未配置"
fi

echo ""

# ============================================
# 10. 代码质量检查
# ============================================
echo "🎨 代码质量检查..."

# Black检查
if command -v black &> /dev/null; then
    if black . --check --line-length=100 --exclude '^apps/bi/(analytics|realtime)/' &> /dev/null; then
        check_pass "Black代码格式检查通过"
    else
        check_warn "Black检查发现问题（运行 black . --line-length=100 修复）"
    fi
fi

# flake8检查
if command -v flake8 &> /dev/null; then
    FLAKE8_ISSUES=$(flake8 . --max-line-length=100 --ignore=E203,W503 --exclude=migrations 2>&1 | wc -l)
    if [ "$FLAKE8_ISSUES" -eq 0 ]; then
        check_pass "flake8代码检查通过"
    else
        check_warn "flake8发现问题: $FLAKE8_ISSUES 个问题"
    fi
fi

echo ""

# ============================================
# 总结
# ============================================
echo "=========================================="
echo "健康检查完成"
echo "=========================================="
echo ""

if [ "$FAILS" -eq 0 ]; then
    echo -e "${GREEN}✓ 所有检查通过！${NC}"
    echo "  通过: $PASSES"
    echo "  失败: $FAILS"
    echo ""
    echo "🎉 系统健康状况良好！"
    exit 0
elif [ "$FAILS" -le 3 ]; then
    echo -e "${YELLOW}⚠ 系统基本正常，但有少量问题${NC}"
    echo "  通过: $PASSES"
    echo "  失败: $FAILS"
    echo ""
    echo "建议修复失败项以获得最佳性能。"
    exit 1
else
    echo -e "${RED}✗ 系统存在多个问题，需要立即处理${NC}"
    echo "  通过: $PASSES"
    echo "  失败: $FAILS"
    echo ""
    echo "请修复失败项后再部署或运行系统。"
    exit 1
fi
