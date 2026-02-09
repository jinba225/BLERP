#!/bin/bash
# 采购订单默认值功能验证脚本

echo "=========================================="
echo "采购订单默认值功能验证"
echo "=========================================="
echo ""

# 检查1: Warehouse模型是否有get_main_warehouse方法
echo "1️⃣  检查 Warehouse.get_main_warehouse() 方法..."
if grep -q "def get_main_warehouse" apps/inventory/models.py; then
    echo "   ✅ get_main_warehouse() 方法已添加"
else
    echo "   ❌ get_main_warehouse() 方法未找到"
fi
echo ""

# 检查2: 视图是否包含默认值逻辑
echo "2️⃣  检查视图层默认值逻辑..."
if grep -q "default_buyer = request.user" apps/purchase/views.py; then
    echo "   ✅ 默认采购员逻辑已添加"
else
    echo "   ❌ 默认采购员逻辑未找到"
fi

if grep -q "default_warehouse = Warehouse.get_main_warehouse()" apps/purchase/views.py; then
    echo "   ✅ 默认收货仓库逻辑已添加"
else
    echo "   ❌ 默认收货仓库逻辑未找到"
fi
echo ""

# 检查3: 模板是否包含默认值条件
echo "3️⃣  检查模板层默认选中逻辑..."
if grep -q "action == 'create' and default_buyer" templates/modules/purchase/order_form.html; then
    echo "   ✅ 采购员默认选中逻辑已添加"
else
    echo "   ❌ 采购员默认选中逻辑未找到"
fi

if grep -q "action == 'create' and default_warehouse" templates/modules/purchase/order_form.html; then
    echo "   ✅ 收货仓库默认选中逻辑已添加"
else
    echo "   ❌ 收货仓库默认选中逻辑未找到"
fi
echo ""

# 检查4: 数据库中是否存在主仓库
echo "4️⃣  检查数据库主仓库配置..."
echo "   请手动验证: python manage.py shell -c \"from inventory.models import Warehouse; print(Warehouse.objects.filter(warehouse_type='main', is_active=True).count())\""
echo ""

echo "=========================================="
echo "验证完成！"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 启动服务器: python manage.py runserver"
echo "2. 访问: http://127.0.0.1:8000/purchase/orders/create/"
echo "3. 验证："
echo "   - 采购员字段是否默认选中当前登录用户"
echo "   - 收货仓库字段是否默认选中主仓库"
echo ""
