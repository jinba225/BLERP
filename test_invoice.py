"""
测试发票功能的脚本
"""
from decimal import Decimal
from datetime import date
from apps.finance.models import Invoice, InvoiceItem
from apps.suppliers.models import Supplier
from apps.customers.models import Customer
from apps.products.models import Product
from apps.core.utils import DocumentNumberGenerator
from django.contrib.auth import get_user_model

User = get_user_model()

def test_invoice_creation():
    """测试发票创建和自动计算功能"""

    print("=" * 60)
    print("开始测试发票功能...")
    print("=" * 60)

    # 1. 获取测试数据
    supplier = Supplier.objects.filter(is_deleted=False).first()
    customer = Customer.objects.filter(is_deleted=False).first()
    products = list(Product.objects.filter(is_deleted=False)[:3])
    user = User.objects.first()

    print(f"\n✓ 找到供应商: {supplier.name if supplier else '无'}")
    print(f"✓ 找到客户: {customer.name if customer else '无'}")
    print(f"✓ 找到产品数量: {len(products)}")
    print(f"✓ 找到用户: {user.username if user else '无'}")

    # 2. 创建采购发票
    print("\n" + "-" * 60)
    print("创建采购发票...")
    print("-" * 60)

    purchase_invoice_number = DocumentNumberGenerator.generate('invoice')
    purchase_invoice = Invoice.objects.create(
        invoice_number=purchase_invoice_number,
        invoice_type='purchase',
        supplier=supplier,
        invoice_date=date.today(),
        tax_rate=Decimal('13.00'),
        status='draft',
        created_by=user
    )

    print(f"✓ 采购发票创建成功")
    print(f"  发票号: {purchase_invoice.invoice_number}")
    print(f"  供应商: {purchase_invoice.supplier.name}")
    print(f"  税率: {purchase_invoice.tax_rate}%")

    # 3. 添加发票明细
    print("\n添加发票明细...")
    items_data = [
        {
            'description': products[0].name if products else '测试产品1',
            'specification': products[0].specifications if products else 'SP-001',
            'unit': products[0].unit if products else '个',
            'quantity': Decimal('10.0000'),
            'unit_price': Decimal('100.00'),
        },
        {
            'description': products[1].name if len(products) > 1 else '测试产品2',
            'specification': products[1].specifications if len(products) > 1 else 'SP-002',
            'unit': products[1].unit if len(products) > 1 else '个',
            'quantity': Decimal('5.0000'),
            'unit_price': Decimal('200.00'),
        },
    ]

    for i, item_data in enumerate(items_data, 1):
        item = InvoiceItem.objects.create(
            invoice=purchase_invoice,
            product=products[i-1] if i <= len(products) else None,
            **item_data
        )
        print(f"  ✓ 明细{i}: {item.description} x {item.quantity} @ ¥{item.unit_price} = ¥{item.amount}")

    # 计算发票总额
    purchase_invoice.calculate_totals()
    purchase_invoice.save()

    # 4. 重新加载发票以获取更新后的总额
    purchase_invoice.refresh_from_db()

    print(f"\n" + "-" * 60)
    print("发票总额计算结果:")
    print("-" * 60)
    print(f"  不含税金额: ¥{purchase_invoice.amount_excluding_tax}")
    print(f"  税额:       ¥{purchase_invoice.tax_amount}")
    print(f"  价税合计:   ¥{purchase_invoice.total_amount}")

    # 5. 验证计算正确性
    expected_amount = Decimal('2000.00')  # 10*100 + 5*200
    expected_tax = expected_amount * purchase_invoice.tax_rate / 100
    expected_total = expected_amount + expected_tax

    print(f"\n" + "-" * 60)
    print("验证计算正确性:")
    print("-" * 60)

    amount_match = purchase_invoice.amount_excluding_tax == expected_amount
    tax_match = purchase_invoice.tax_amount == expected_tax
    total_match = purchase_invoice.total_amount == expected_total

    print(f"  不含税金额: {'✓' if amount_match else '✗'} (期望: ¥{expected_amount}, 实际: ¥{purchase_invoice.amount_excluding_tax})")
    print(f"  税额:       {'✓' if tax_match else '✗'} (期望: ¥{expected_tax}, 实际: ¥{purchase_invoice.tax_amount})")
    print(f"  价税合计:   {'✓' if total_match else '✗'} (期望: ¥{expected_total}, 实际: ¥{purchase_invoice.total_amount})")

    # 6. 创建销售发票
    print("\n" + "-" * 60)
    print("创建销售发票...")
    print("-" * 60)

    sales_invoice_number = DocumentNumberGenerator.generate('invoice')
    sales_invoice = Invoice.objects.create(
        invoice_number=sales_invoice_number,
        invoice_type='sales',
        customer=customer,
        invoice_date=date.today(),
        tax_rate=Decimal('13.00'),
        status='draft',
        created_by=user
    )

    print(f"✓ 销售发票创建成功")
    print(f"  发票号: {sales_invoice.invoice_number}")
    print(f"  客户: {sales_invoice.customer.name}")

    # 7. 添加销售发票明细
    print("\n添加销售发票明细...")
    InvoiceItem.objects.create(
        invoice=sales_invoice,
        product=products[2] if len(products) > 2 else None,
        description=products[2].name if len(products) > 2 else '测试产品3',
        specification=products[2].specifications if len(products) > 2 else 'SP-003',
        unit=products[2].unit if len(products) > 2 else '个',
        quantity=Decimal('20.0000'),
        unit_price=Decimal('150.00'),
    )

    # 计算销售发票总额
    sales_invoice.calculate_totals()
    sales_invoice.save()

    sales_invoice.refresh_from_db()
    print(f"  ✓ 明细添加成功")
    print(f"  价税合计: ¥{sales_invoice.total_amount}")

    # 8. 统计总览
    print("\n" + "=" * 60)
    print("测试完成！数据统计:")
    print("=" * 60)

    total_invoices = Invoice.objects.filter(is_deleted=False).count()
    total_items = InvoiceItem.objects.filter(invoice__is_deleted=False).count()
    purchase_count = Invoice.objects.filter(is_deleted=False, invoice_type='purchase').count()
    sales_count = Invoice.objects.filter(is_deleted=False, invoice_type='sales').count()

    print(f"  发票总数:   {total_invoices}")
    print(f"  - 采购发票: {purchase_count}")
    print(f"  - 销售发票: {sales_count}")
    print(f"  明细总数:   {total_items}")

    print("\n" + "=" * 60)
    print("✓ 所有测试通过！")
    print("=" * 60)

    return purchase_invoice, sales_invoice

if __name__ == '__main__':
    purchase_invoice, sales_invoice = test_invoice_creation()
