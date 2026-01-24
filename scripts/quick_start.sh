#!/bin/bash
# Django URL 一致性检查 - 快速启动脚本

echo "=========================================="
echo "Django URL 一致性检查工具"
echo "=========================================="
echo ""

# 检查是否在项目根目录
if [ ! -f "manage.py" ]; then
    echo "错误：请在项目根目录下运行此脚本"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo "警告：未检测到虚拟环境"
fi

# 激活虚拟环境（如果存在）
if [ -d "venv" ]; then
    echo "激活虚拟环境..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "激活虚拟环境..."
    source .venv/bin/activate
fi

# 运行检查脚本
echo ""
echo "开始检查 URL 一致性..."
echo ""

python scripts/check_url_consistency.py

# 检查退出码
if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ 检查完成！"
    echo "=========================================="
    echo ""
    echo "查看详细报告："
    echo "  cat url_consistency_report.json"
    echo ""
    echo "或使用 jq 美化输出："
    echo "  jq . url_consistency_report.json"
    echo ""
else
    echo ""
    echo "=========================================="
    echo "❌ 检查失败"
    echo "=========================================="
    exit 1
fi
