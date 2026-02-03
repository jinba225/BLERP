#!/bin/bash
# Django 开发服务器启动脚本

echo "========================================="
echo "  Django ERP 启动脚本"
echo "========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查数据库
echo -e "${BLUE}[1/6]${NC} 检查数据库..."
if [ -f "db.sqlite3" ]; then
    echo -e "${GREEN}✓${NC} 数据库文件存在"
else
    echo -e "${RED}✗${NC} 数据库文件不存在"
    exit 1
fi

# 检查.env文件
echo -e "${BLUE}[2/6]${NC} 检查.env配置..."
if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC} .env 文件存在"
else
    echo -e "${RED}✗${NC} .env 文件不存在"
    exit 1
fi

# 检查DEBUG设置
DEBUG=$(grep "^DEBUG=" .env | cut -d'=' -f2)
if [ "$DEBUG" = "False" ]; then
    echo -e "${GREEN}✓${NC} DEBUG=False (生产模式)"
elif [ "$DEBUG" = "True" ]; then
    echo -e "${YELLOW}⚠${NC} DEBUG=True (开发模式)"
else
    echo -e "${RED}✗${NC} DEBUG 未正确设置"
    exit 1
fi

# 运行Django检查
echo -e "${BLUE}[3/6]${NC} 运行Django系统检查..."
python manage.py check 2>&1 | head -1
CHECK_RESULT=$?
if [ $CHECK_RESULT -eq 0 ]; then
    echo -e "${GREEN}✓${NC} 系统检查通过"
else
    echo -e "${RED}✗${NC} 系统检查失败 (退出码: $CHECK_RESULT)"
    exit 1
fi

# 运行Django部署检查
echo ""
echo -e "${BLUE}[4/6]${NC} 运行生产环境检查..."
DEPLOY_WARNINGS=$(python manage.py check --deploy 2>&1 | grep -c "^?:")
echo -e "发现 $DEPLOY_WARNINGS 个部署警告"
echo -e "${GREEN}✓${NC} 部署检查完成"

# 运行迁移（如果需要）
echo ""
read -p "是否需要运行迁移? (y/n)" -n 1 -r
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}[5/6]${NC} 运行数据库迁移..."
    python manage.py migrate --run-syncdb 2>&1 | tail -5
    echo -e "${GREEN}✓${NC} 迁移完成"
fi

# 收集静态文件（如果需要）
echo ""
read -p "是否需要收集静态文件? (y/n)" -n 1 -r
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}[6/6]${NC} 收集静态文件..."
    python manage.py collectstatic --noinput 2>&1 | tail -5
    echo -e "${GREEN}✓${NC} 静态文件收集完成"
fi

# 启动开发服务器
echo ""
echo "========================================="
echo -e "${GREEN}准备启动服务器...${NC}"
echo "========================================="
echo ""
echo -e "${YELLOW}服务器地址:${NC} http://0.0.0.0:8000"
echo -e "${YELLOW}API文档:${NC}   http://0.0.0.0:8000/api/docs/"
echo ""
echo "按 ${RED}Ctrl+C${NC} 停止服务器"
echo ""
python manage.py runserver 0.0.0.0:8000
