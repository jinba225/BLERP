#!/bin/bash
# 页面自动刷新系统验证脚本

echo "================================"
echo "Django ERP 页面自动刷新系统验证"
echo "================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查函数
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1"
        return 0
    else
        echo -e "${RED}✗${NC} $1 (未找到)"
        return 1
    fi
}

check_config() {
    if grep -q "$1" "$2" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $2 包含 $1"
        return 0
    else
        echo -e "${RED}✗${NC} $2 缺少 $1"
        return 1
    fi
}

echo "1. 检查核心文件..."
check_file "django_erp/settings.py"
check_file "apps/core/context_processors.py"
check_file "static/js/modules/page-refresh.js"
check_file "templates/layouts/base.html"
check_file "apps/core/views.py"
check_file "templates/modules/core/page_refresh_demo.html"
echo ""

echo "2. 检查配置..."
check_config "PAGE_REFRESH_CONFIG" "django_erp/settings.py"
check_config "page_refresh_config" "apps/core/context_processors.py"
check_config "core.context_processors.page_refresh_config" "django_erp/settings.py"
echo ""

echo "3. 检查JavaScript模块..."
if grep -q "PageRefreshManager" "static/js/modules/page-refresh.js"; then
    echo -e "${GREEN}✓${NC} PageRefreshManager 类已定义"
else
    echo -e "${RED}✗${NC} PageRefreshManager 类未找到"
fi

if grep -q "usePageRefresh" "templates/layouts/base.html"; then
    echo -e "${GREEN}✓${NC} Alpine.js 组件已注册"
else
    echo -e "${RED}✗${NC} Alpine.js 组件未找到"
fi
echo ""

echo "4. 运行Django系统检查..."
cd /Users/janjung/Code_Projects/django_erp
if python manage.py check > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Django 系统检查通过"
else
    echo -e "${RED}✗${NC} Django 系统检查失败"
    python manage.py check
fi
echo ""

echo "5. 检查静态文件..."
if [ -d "static/js/modules" ]; then
    echo -e "${GREEN}✓${NC} static/js/modules 目录存在"
else
    echo -e "${RED}✗${NC} static/js/modules 目录不存在"
fi
echo ""

echo "================================"
echo "验证完成！"
echo "================================"
echo ""
echo "下一步操作："
echo "1. 启动开发服务器: python manage.py runserver"
echo "2. 访问演示页面: http://127.0.0.1:8000/page-refresh-demo/"
echo "3. 打开浏览器控制台查看日志"
echo "4. 测试自动刷新和手动刷新功能"
echo ""
echo "配置信息："
echo "- 全局开关: PAGE_REFRESH_CONFIG['enabled'] = True"
echo "- 默认间隔: 30秒 (开发环境15秒)"
echo "- Context Processor: core.context_processors.page_refresh_config"
echo "- Alpine.js 组件: usePageRefresh"
echo ""
