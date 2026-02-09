#!/bin/bash
# Django 开发服务器启动脚本（智能重载）
# 解决装饰器修改不生效的问题

echo "🔄 Django 开发服务器启动脚本"
echo "================================"

# 检查是否安装了 watchfiles
if python3 -c "import watchfiles" 2>/dev/null; then
    echo "✅ 检测到 watchfiles，使用智能重载模式"
    echo ""
    echo "🚀 启动服务器..."
    watchfiles run python3 manage.py runserver
else
    echo "⚠️  未安装 watchfiles，使用 Django 默认重载"
    echo ""
    echo "💡 安装 watchfiles 以获得更好的重载体验："
    echo "   pip install watchfiles"
    echo ""
    echo "🚀 启动服务器..."
    python3 manage.py runserver
fi
