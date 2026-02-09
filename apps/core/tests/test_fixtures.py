"""
测试数据工厂

提供便捷的方法创建测试数据，用于E2E测试
"""

from decimal import Decimal
from django.utils import timezone
from django.contrib.auth import get_user_model


User = get_user_model()


class FixtureFactory:
    """测试数据工厂基类"""

    @staticmethod
    def create_product(code='PROD001', name='测试产品',
                      cost_price=Decimal('100.00'),
                      selling_price=Decimal('150.00'), **kwargs):
        """
        创建产品

        Args:
            code: 产品代码
            name: 产品名称
            cost_price: 成本价
            selling_price: 销售价
            **kwargs: 其他Product字段

        Returns:
            Product: 产品实例
        """
        from products.models import Product, ProductCategory, Unit

        # 获取或创建默认单位
        unit = kwargs.pop('unit', None)
        if not unit:
            unit, _ = Unit.objects.get_or_create(
                name='件',
                defaults={
                    'symbol': '件',
                    'unit_type': 'count',
                    'is_default': True
                }
            )

        # 获取或创建默认分类
        category = kwargs.pop('category', None)
        if not category:
            category, _ = ProductCategory.objects.get_or_create(
                code='CAT001',
                defaults={
                    'name': '默认分类'
                }
            )

        return Product.objects.create(
            code=code,
            name=name,
            cost_price=cost_price,
            selling_price=selling_price,
            unit=unit,
            category=category,
            **kwargs
        )

    @staticmethod
    def create_supplier(code='SUP001', name='测试供应商', **kwargs):
        """
        创建供应商

        Args:
            code: 供应商代码
            name: 供应商名称
            **kwargs: 其他Supplier字段

        Returns:
            Supplier: 供应商实例
        """
        from suppliers.models import Supplier

        defaults = {
            'address': '测试地址',
            'city': '测试城市',
            'payment_terms': 'bank_transfer'
        }
        defaults.update(kwargs)

        return Supplier.objects.create(
            code=code,
            name=name,
            **defaults
        )

    @staticmethod
    def create_customer(code='CUS001', name='测试客户', **kwargs):
        """
        创建客户

        Args:
            code: 客户代码
            name: 客户名称
            **kwargs: 其他Customer字段

        Returns:
            Customer: 客户实例
        """
        from customers.models import Customer

        defaults = {
            'address': '客户地址',
            'city': '客户城市'
        }
        defaults.update(kwargs)

        return Customer.objects.create(
            code=code,
            name=name,
            **defaults
        )

    @staticmethod
    def create_warehouse(code='WH001', name='测试仓库',
                        warehouse_type='main', **kwargs):
        """
        创建仓库

        Args:
            code: 仓库代码
            name: 仓库名称
            warehouse_type: 仓库类型
            **kwargs: 其他Warehouse字段

        Returns:
            Warehouse: 仓库实例
        """
        from inventory.models import Warehouse

        defaults = {
            'is_active': True
        }
        defaults.update(kwargs)

        return Warehouse.objects.create(
            code=code,
            name=name,
            warehouse_type=warehouse_type,
            **defaults
        )

    @staticmethod
    def create_purchase_order(user, supplier, items_data, **kwargs):
        """
        创建采购订单

        Args:
            user: 创建用户
            supplier: 供应商
            items_data: 订单明细列表
                [{'product': product, 'quantity': 100, 'unit_price': 10}, ...]
            **kwargs: 其他PurchaseOrder字段

        Returns:
            PurchaseOrder: 采购订单实例
        """
        from purchase.models import PurchaseOrder, PurchaseOrderItem

        defaults = {
            'order_date': timezone.now().date(),
            'required_date': timezone.now().date() + timezone.timedelta(days=7),
        }
        defaults.update(kwargs)

        order = PurchaseOrder.objects.create(
            supplier=supplier,
            created_by=user,
            **defaults
        )

        # 创建订单明细
        for item_data in items_data:
            product = item_data.pop('product')
            PurchaseOrderItem.objects.create(
                purchase_order=order,
                product=product,
                **item_data
            )

        # 重新计算总金额
        order.calculate_totals()

        return order

    @staticmethod
    def create_sales_order(user, customer, items_data, **kwargs):
        """
        创建销售订单

        Args:
            user: 创建用户
            customer: 客户
            items_data: 订单明细列表
                [{'product': product, 'quantity': 100, 'unit_price': 15}, ...]
            **kwargs: 其他SalesOrder字段

        Returns:
            SalesOrder: 销售订单实例
        """
        from sales.models import SalesOrder, SalesOrderItem

        defaults = {
            'order_date': timezone.now().date(),
            'required_date': timezone.now().date() + timezone.timedelta(days=7),
        }
        defaults.update(kwargs)

        order = SalesOrder.objects.create(
            customer=customer,
            created_by=user,
            **defaults
        )

        # 创建订单明细
        for item_data in items_data:
            product = item_data.pop('product')
            SalesOrderItem.objects.create(
                order=order,
                product=product,
                **item_data
            )

        # 重新计算总金额
        order.calculate_totals()

        return order

    @staticmethod
    def create_purchase_receipt(order, warehouse, user, items_data, **kwargs):
        """
        创建采购收货单

        Args:
            order: 采购订单
            warehouse: 收货仓库
            user: 创建用户
            items_data: 收货明细列表
                [{'order_item': order_item, 'quantity': 50, 'unit_price': 10}, ...]
            **kwargs: 其他PurchaseReceipt字段

        Returns:
            PurchaseReceipt: 收货单实例
        """
        from purchase.models import PurchaseReceipt, PurchaseReceiptItem

        defaults = {
            'receipt_date': timezone.now().date(),
        }
        defaults.update(kwargs)

        receipt = PurchaseReceipt.objects.create(
            purchase_order=order,
            warehouse=warehouse,
            created_by=user,
            **defaults
        )

        # 创建收货明细
        for item_data in items_data:
            order_item = item_data.pop('order_item')
            received_quantity = item_data.pop('quantity')
            # 移除不存在的字段
            item_data.pop('unit_price', None)
            item_data.pop('product', None)
            PurchaseReceiptItem.objects.create(
                receipt=receipt,
                order_item=order_item,
                received_quantity=received_quantity,
                **item_data
            )

        # 重新计算总金额（如果模型有此方法）
        # receipt.calculate_totals()

        return receipt

    @staticmethod
    def create_sales_delivery(order, warehouse, user, items_data, **kwargs):
        """
        创建销售发货单

        Args:
            order: 销售订单
            warehouse: 发货仓库
            user: 创建用户
            items_data: 发货明细列表
                [{'order_item': order_item, 'quantity': 50}, ...]
            **kwargs: 其他Delivery字段

        Returns:
            Delivery: 发货单实例
        """
        from sales.models import Delivery, DeliveryItem

        defaults = {
            'planned_date': timezone.now().date(),  # 修复: 使用planned_date而不是delivery_date
        }
        defaults.update(kwargs)

        delivery = Delivery.objects.create(
            sales_order=order,
            warehouse=warehouse,
            created_by=user,
            **defaults
        )

        # 创建发货明细
        for item_data in items_data:
            order_item = item_data.pop('order_item')
            quantity = item_data.pop('quantity', item_data.get('quantity'))
            DeliveryItem.objects.create(
                delivery=delivery,
                order_item=order_item,
                quantity=quantity,
                **item_data
            )

        # 重新计算总金额（如果模型有此方法）
        # delivery.calculate_totals()

        return delivery
