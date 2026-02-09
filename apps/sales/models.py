"""
Sales models for the ERP system.
"""
from datetime import timedelta
from decimal import Decimal

from core.models import PAYMENT_METHOD_CHOICES, BaseModel
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

User = get_user_model()


class SalesOrder(BaseModel):
    """
    Sales order model.
    """

    ORDER_STATUS = [
        ("draft", "草稿"),
        ("pending", "待审核"),
        ("confirmed", "已确认"),
        ("in_production", "生产中"),
        ("ready_to_ship", "待发货"),
        ("shipped", "已发货"),
        ("delivered", "已交付"),
        ("completed", "已完成"),
        ("cancelled", "已取消"),
    ]

    PAYMENT_STATUS = [
        ("unpaid", "未付款"),
        ("partial", "部分付款"),
        ("paid", "已付款"),
        ("overdue", "逾期"),
    ]

    INVOICE_STATUS = [
        ("not_invoiced", "未开票"),
        ("partial_invoiced", "部分开票"),
        ("invoiced", "已开票"),
        ("red_flushed", "红冲"),
    ]

    # Order information
    order_number = models.CharField("订单号", max_length=100, unique=True)
    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.CASCADE,
        related_name="sales_orders",
        verbose_name="客户",
    )
    status = models.CharField("订单状态", max_length=20, choices=ORDER_STATUS, default="draft")
    payment_status = models.CharField(
        "付款状态", max_length=20, choices=PAYMENT_STATUS, default="unpaid"
    )
    invoice_status = models.CharField(
        "开票状态", max_length=20, choices=INVOICE_STATUS, default="not_invoiced"
    )

    # Dates
    order_date = models.DateField("订单日期")
    required_date = models.DateField("要求交期", null=True, blank=True)
    promised_date = models.DateField("承诺交期", null=True, blank=True)
    shipped_date = models.DateField("发货日期", null=True, blank=True)

    # Sales information
    sales_rep = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sales_orders",
        verbose_name="销售代表",
    )

    # Financial information
    subtotal = models.DecimalField(
        "含税小计", max_digits=12, decimal_places=2, default=0, help_text="所有明细的含税金额之和"
    )
    tax_rate = models.DecimalField("税率(%)", max_digits=5, decimal_places=2, default=13)
    tax_amount = models.DecimalField(
        "税额", max_digits=12, decimal_places=2, default=0, help_text="从含税价格反推得出"
    )
    discount_rate = models.DecimalField("折扣率(%)", max_digits=5, decimal_places=2, default=0)
    discount_amount = models.DecimalField("折扣金额", max_digits=12, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(
        "运费", max_digits=12, decimal_places=2, default=0, help_text="含税运费"
    )
    total_amount = models.DecimalField(
        "含税总金额", max_digits=12, decimal_places=2, default=0, help_text="客户实际支付金额（含税）"
    )
    currency = models.CharField("币种", max_length=10, default="CNY")

    # Shipping information
    shipping_address = models.TextField("收货地址", blank=True)
    shipping_contact = models.CharField("收货联系人", max_length=100, blank=True)
    shipping_phone = models.CharField("收货电话", max_length=20, blank=True)
    shipping_method = models.CharField("配送方式", max_length=100, blank=True)
    tracking_number = models.CharField("快递单号", max_length=100, blank=True)

    # Payment information
    payment_terms = models.CharField("付款方式", max_length=50, blank=True, help_text="从客户信息自动带出")

    # Additional information
    reference_number = models.CharField("客户订单号", max_length=100, blank=True)
    notes = models.TextField("备注", blank=True)
    internal_notes = models.TextField("内部备注", blank=True)

    # Approval
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_sales_orders",
        verbose_name="审核人",
    )
    approved_at = models.DateTimeField("审核时间", null=True, blank=True)

    class Meta:
        verbose_name = "销售订单"
        verbose_name_plural = "销售订单"
        db_table = "sales_order"
        ordering = ["-order_date", "-created_at"]

    def __str__(self):
        return f"{self.order_number} - {self.customer.name}"

    def save(self, *args, **kwargs):
        # Only calculate totals if this is an update (pk exists) or if explicitly requested
        # For new orders, totals will be calculated after items are added
        skip_calculate = kwargs.pop("skip_calculate", False)
        if not skip_calculate and self.pk:
            self.calculate_totals()
        super().save(*args, **kwargs)

    def calculate_totals(self):
        """
        Calculate order totals.
        注意：本系统采用含税价格体系
        - unit_price 是含税单价
        - line_total 是含税行总计
        - total_amount 是含税总金额
        - tax_amount 从含税价反推得出（用于财务核算）
        """
        # Safety check: only calculate if order has been saved (has pk)
        if not self.pk:
            self.subtotal = 0
            self.discount_amount = 0
            self.tax_amount = 0
            self.total_amount = 0
            return

        # 1. 小计 = 所有行的含税总计之和
        self.subtotal = sum([item.line_total for item in self.items.all()])

        # 2. 计算折扣
        # 如果设置了折扣率，则优先使用折扣率计算折扣金额
        if self.discount_rate > 0:
            self.discount_amount = self.subtotal * (self.discount_rate / Decimal("100"))

        # 3. 折后总额（含税，不含运费）= 小计 - 折扣金额
        discounted_total = self.subtotal - self.discount_amount

        # 4. 从含税价反推税额：税额 = 含税价 / (1 + 税率) × 税率
        if self.tax_rate > 0:
            self.tax_amount = (
                discounted_total
                / (Decimal("1") + self.tax_rate / Decimal("100"))
                * (self.tax_rate / Decimal("100"))
            )
        else:
            self.tax_amount = 0

        # 5. 总金额 = 折后含税金额 + 运费（运费通常也是含税的）
        self.total_amount = discounted_total + self.shipping_cost

    @property
    def is_overdue(self):
        """Check if order is overdue."""
        from django.utils import timezone

        if self.required_date and self.status not in ["completed", "cancelled"]:
            return timezone.now().date() > self.required_date
        return False

    def approve_order(self, approved_by_user, warehouse=None, auto_create_delivery=None):
        from core.models import SystemConfig
        from core.utils.document_number import DocumentNumberGenerator
        from django.utils import timezone

        # Check if already approved
        if self.approved_by:
            raise ValueError("订单已经审核过了")

        # Check if order has items
        if not self.items.exists():
            raise ValueError("订单没有明细，无法审核")

        # Update order status
        self.approved_by = approved_by_user
        self.approved_at = timezone.now()
        self.status = "confirmed"
        self.save()

        # Check if should auto create delivery
        if auto_create_delivery is None:
            # Check system configuration
            config = SystemConfig.objects.filter(
                key="sales_auto_create_delivery_on_approve", is_active=True
            ).first()
            auto_create_delivery = config.value.lower() == "true" if config else True

        delivery = None
        if auto_create_delivery:
            # 1. Create Delivery (出库单)
            if not warehouse:
                # Try to get default warehouse
                from inventory.models import Warehouse

                warehouse = Warehouse.objects.filter(is_active=True).first()
                if not warehouse:
                    raise ValueError("没有可用的仓库，请先创建仓库")

            # Get primary contact info from CustomerContact if not specified
            primary_contact = (
                self.customer.contacts.filter(is_primary=True).first()
                if not self.shipping_contact
                else None
            )
            default_contact_name = primary_contact.name if primary_contact else ""
            default_contact_phone = primary_contact.mobile if primary_contact else ""

            delivery = Delivery.objects.create(
                delivery_number=DocumentNumberGenerator.generate("delivery"),
                sales_order=self,
                status="preparing",
                planned_date=self.required_date or timezone.now().date(),
                shipping_address=self.shipping_address or self.customer.address,
                shipping_contact=self.shipping_contact or default_contact_name,
                shipping_phone=self.shipping_phone or default_contact_phone,
                shipping_method=self.shipping_method,
                warehouse=warehouse,
                created_by=approved_by_user,
            )

            # Create delivery items from order items (full quantity)
            for order_item in self.items.all():
                DeliveryItem.objects.create(
                    delivery=delivery,
                    order_item=order_item,
                    quantity=order_item.remaining_quantity,  # Use remaining quantity for partial delivery support
                    created_by=approved_by_user,
                )

        # 2. Create Customer Account (应收账款)
        from finance.models import CustomerAccount

        # Calculate due date based on payment terms
        due_date = None
        if self.payment_terms == "net_30":
            due_date = timezone.now().date() + timedelta(days=30)
        elif self.payment_terms == "net_60":
            due_date = timezone.now().date() + timedelta(days=60)

        account = CustomerAccount.objects.create(
            customer=self.customer,
            sales_order=self,
            invoice_amount=self.total_amount,
            # exclude_tax_amount removed as it is not in the model
            balance=self.total_amount,
            currency=self.currency,
            due_date=due_date,
            created_by=approved_by_user,
        )

        return (delivery, account)

    def unapprove_order(self):
        """
        Unapprove (cancel approval) sales order.
        This will:
        1. Delete related deliveries (that haven't been shipped)
        2. Delete related customer accounts (that haven't been paid)
        3. Reset approval information
        4. Change status back to draft

        Raises:
            ValueError: If order cannot be unapproved
        """
        from django.utils import timezone

        # Check if order is approved
        if not self.approved_by:
            raise ValueError("订单未审核，无法撤销")

        # Check order status - can only unapprove if not shipped or completed
        if self.status in ["shipped", "delivered", "completed"]:
            raise ValueError(f"订单状态为 {self.get_status_display()}，无法撤销审核")

        # Check deliveries - cannot unapprove if any delivery has been shipped
        for delivery in self.deliveries.all():
            if delivery.status in ["shipped", "in_transit", "delivered"]:
                raise ValueError(f"发货单 {delivery.delivery_number} 已发货，无法撤销审核")

        # Check customer accounts - cannot unapprove if any payment has been made
        from finance.models import CustomerAccount

        for account in CustomerAccount.objects.filter(sales_order=self):
            if account.paid_amount > 0:
                raise ValueError("订单已有收款记录，无法撤销审核")

        # Delete related deliveries and their items
        for delivery in self.deliveries.all():
            delivery.items.all().delete()
            delivery.delete()

        # Delete related customer accounts
        CustomerAccount.objects.filter(sales_order=self).delete()

        # Reset approval information
        self.approved_by = None
        self.approved_at = None
        self.status = "draft"
        self.save()

        return True


class SalesOrderItem(BaseModel):
    """
    Sales order item model.
    """

    order = models.ForeignKey(
        SalesOrder, on_delete=models.CASCADE, related_name="items", verbose_name="销售订单"
    )
    product = models.ForeignKey("products.Product", on_delete=models.CASCADE, verbose_name="产品")
    quantity = models.IntegerField("数量")
    unit_price = models.DecimalField("含税单价", max_digits=12, decimal_places=2, help_text="含税单价")
    discount_rate = models.DecimalField("折扣率(%)", max_digits=5, decimal_places=2, default=0)
    discount_amount = models.DecimalField("折扣金额", max_digits=12, decimal_places=2, default=0)
    line_total = models.DecimalField(
        "含税小计", max_digits=12, decimal_places=2, default=0, help_text="含税金额"
    )

    # Delivery information
    delivered_quantity = models.IntegerField("已交付数量", default=0)
    required_date = models.DateField("要求交期", null=True, blank=True)

    # Production information
    produced_quantity = models.IntegerField("已生产数量", default=0)

    notes = models.TextField("备注", blank=True)
    sort_order = models.PositiveIntegerField("排序", default=0)

    class Meta:
        verbose_name = "销售订单明细"
        verbose_name_plural = "销售订单明细"
        db_table = "sales_order_item"
        ordering = ["sort_order"]

    def __str__(self):
        return f"{self.order.order_number} - {self.product.name}"

    def save(self, *args, **kwargs):
        # Calculate line total
        from decimal import Decimal

        discount_rate_decimal = Decimal(str(self.discount_rate)) / Decimal("100")
        self.discount_amount = self.quantity * self.unit_price * discount_rate_decimal
        self.line_total = (self.quantity * self.unit_price) - self.discount_amount
        super().save(*args, **kwargs)

    @property
    def remaining_quantity(self):
        """Calculate remaining quantity to deliver."""
        return self.quantity - self.delivered_quantity


class Quote(BaseModel):
    """
    Sales quote model.
    """

    QUOTE_STATUS = [
        ("draft", "草稿"),
        ("sent", "已发送"),
        ("accepted", "已接受"),
        ("rejected", "已拒绝"),
        ("expired", "已过期"),
        ("converted", "已转订单"),
    ]

    QUOTE_TYPES = [
        ("domestic", "国内报价"),
        ("overseas", "海外报价"),
    ]

    # Quote information
    quote_number = models.CharField("报价单号", max_length=100, unique=True)
    quote_type = models.CharField("报价类型", max_length=20, choices=QUOTE_TYPES, default="domestic")
    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.CASCADE, related_name="quotes", verbose_name="客户"
    )
    contact_person = models.ForeignKey(
        "customers.CustomerContact",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="联系人",
    )
    status = models.CharField("状态", max_length=20, choices=QUOTE_STATUS, default="draft")

    # Dates
    quote_date = models.DateField("报价日期")
    valid_until = models.DateField("有效期至")

    # Sales information
    sales_rep = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="quotes",
        verbose_name="销售代表",
    )

    # Financial information
    currency = models.CharField("币种", max_length=10, default="CNY")
    exchange_rate = models.DecimalField("汇率", max_digits=10, decimal_places=4, default=1.0000)
    subtotal = models.DecimalField(
        "含税小计", max_digits=12, decimal_places=2, default=0, help_text="所有明细的含税金额之和"
    )
    tax_rate = models.DecimalField("税率(%)", max_digits=5, decimal_places=2, default=13)
    tax_amount = models.DecimalField(
        "税额", max_digits=12, decimal_places=2, default=0, help_text="从含税价格反推得出"
    )
    discount_rate = models.DecimalField("折扣率(%)", max_digits=5, decimal_places=2, default=0)
    discount_amount = models.DecimalField("折扣金额", max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(
        "含税总金额", max_digits=12, decimal_places=2, default=0, help_text="客户实际支付金额（含税）"
    )
    total_amount_cny = models.DecimalField(
        "总金额(CNY)", max_digits=12, decimal_places=2, default=0, help_text="自动转换为人民币"
    )

    # Terms and conditions
    payment_terms = models.CharField("付款方式", max_length=50, blank=True, help_text="从客户信息自动带出")
    delivery_terms = models.CharField("交货条件", max_length=200, blank=True)
    warranty_terms = models.TextField("质保条款", blank=True)

    # Additional information
    reference_number = models.CharField("客户询价号", max_length=100, blank=True)
    notes = models.TextField("备注", blank=True)

    # Conversion information
    converted_order = models.ForeignKey(
        SalesOrder, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="转换的订单"
    )

    class Meta:
        verbose_name = "销售报价"
        verbose_name_plural = "销售报价"
        db_table = "sales_quote"
        ordering = ["-quote_date", "-created_at"]

    def __str__(self):
        return f"{self.quote_number} - {self.customer.name}"

    def save(self, *args, **kwargs):
        # Only calculate totals if this is an update (pk exists) or if explicitly requested
        # For new quotes, totals will be calculated after items are added
        skip_calculate = kwargs.pop("skip_calculate", False)
        if not skip_calculate and self.pk:
            self.calculate_totals()
        super().save(*args, **kwargs)

    def calculate_totals(self):
        """
        Calculate quote totals.
        注意：本系统采用含税价格体系
        - unit_price 是含税单价
        - line_total 是含税行总计（已应用明细行折扣）
        - total_amount 是含税总金额
        - tax_amount 从含税价反推得出（用于财务核算）

        注：支持明细行折扣和整单折扣
        """
        # Safety check: only calculate if quote has been saved (has pk)
        if not self.pk:
            self.subtotal = 0
            # Keep discount_amount as is (may be set from form)
            self.tax_amount = 0
            self.total_amount = 0
            self.total_amount_cny = 0
            return

        # 1. 小计 = 所有行的含税总计之和（已包含明细行折扣）
        self.subtotal = sum([item.line_total for item in self.items.all()])

        # 2. 整单折扣金额（从表单传入，不重置）
        # discount_amount is preserved from form input

        # 3. 折后总额（含税）= 小计 - 折扣金额
        total_with_tax = self.subtotal - self.discount_amount

        # 4. 从含税价反推税额：税额 = 含税价 / (1 + 税率) × 税率
        #    例如：含税价113元，税率13%，则税额 = 113 / 1.13 × 0.13 = 13元
        if self.tax_rate > 0:
            self.tax_amount = (
                total_with_tax
                / (Decimal("1") + self.tax_rate / Decimal("100"))
                * (self.tax_rate / Decimal("100"))
            )
        else:
            self.tax_amount = 0

        # 5. 总金额 = 折后含税总额
        self.total_amount = total_with_tax

        # 6. Convert to CNY if foreign currency
        if self.currency != "CNY":
            self.total_amount_cny = self.total_amount * self.exchange_rate
        else:
            self.total_amount_cny = self.total_amount

    @property
    def is_expired(self):
        """Check if quote is expired."""
        from django.utils import timezone

        return timezone.now().date() > self.valid_until and self.status not in [
            "converted",
            "accepted",
        ]

    def convert_to_order(self):
        """Convert quote to sales order."""
        if self.status == "converted":
            return self.converted_order

        # Create sales order from quote
        order = SalesOrder.objects.create(
            order_number=self._generate_order_number(),
            customer=self.customer,
            order_date=timezone.now().date(),
            required_date=(timezone.now().date() + timedelta(days=15)),
            sales_rep=self.sales_rep,
            subtotal=self.subtotal,
            tax_rate=self.tax_rate,
            tax_amount=self.tax_amount,
            discount_rate=self.discount_rate,
            discount_amount=self.discount_amount,
            total_amount=self.total_amount,
            currency=self.currency,
            payment_terms=self.payment_terms,
            reference_number=self.quote_number,
            created_by=self.created_by,
        )

        # Copy quote items to order items
        for quote_item in self.items.all():
            SalesOrderItem.objects.create(
                order=order,
                product=quote_item.product,
                quantity=quote_item.quantity,
                unit_price=quote_item.unit_price,
                discount_rate=quote_item.discount_rate,
                discount_amount=quote_item.discount_amount,
                line_total=quote_item.line_total,
                notes=quote_item.notes,
                sort_order=quote_item.sort_order,
                created_by=self.created_by,
            )

        order.calculate_totals()
        order.save()

        # Update quote status
        self.status = "converted"
        self.converted_order = order
        self.save()

        return order

    def _generate_order_number(self):
        """Generate order number from quote number."""
        from core.utils.document_number import DocumentNumberGenerator

        return DocumentNumberGenerator.generate("sales_order")


class QuoteItem(BaseModel):
    """
    Quote item model.
    """

    quote = models.ForeignKey(
        Quote, on_delete=models.CASCADE, related_name="items", verbose_name="报价单"
    )
    product = models.ForeignKey("products.Product", on_delete=models.CASCADE, verbose_name="产品")
    specifications = models.CharField("产品规格", max_length=500, blank=True, help_text="产品规格型号")
    unit = models.CharField("单位", max_length=50, blank=True, help_text="产品单位")
    quantity = models.IntegerField("数量")
    unit_price = models.DecimalField("含税单价", max_digits=12, decimal_places=2, help_text="含税单价")
    discount_rate = models.DecimalField("折扣率(%)", max_digits=5, decimal_places=2, default=0)
    discount_amount = models.DecimalField("折扣金额", max_digits=12, decimal_places=2, default=0)
    tax_rate = models.DecimalField(
        "税率(%)", max_digits=5, decimal_places=2, default=13, help_text="增值税税率，默认13%"
    )
    line_total = models.DecimalField(
        "含税小计", max_digits=12, decimal_places=2, default=0, help_text="含税金额"
    )

    # Delivery information
    lead_time = models.PositiveIntegerField("交货周期(天)", default=0)

    notes = models.TextField("备注", blank=True)
    sort_order = models.PositiveIntegerField("排序", default=0)

    class Meta:
        verbose_name = "报价明细"
        verbose_name_plural = "报价明细"
        db_table = "sales_quote_item"
        ordering = ["sort_order"]

    def __str__(self):
        return f"{self.quote.quote_number} - {self.product.name}"

    def save(self, *args, **kwargs):
        # Calculate discount_amount based on quantity, unit_price, and line_total
        # line_total is either manually entered or calculated by the form/JavaScript
        # discount_amount = (quantity * unit_price) - line_total
        original_amount = self.quantity * self.unit_price
        self.discount_amount = original_amount - self.line_total

        # Ensure discount_amount is not negative
        if self.discount_amount < 0:
            self.discount_amount = 0
            self.line_total = original_amount

        super().save(*args, **kwargs)


class Delivery(BaseModel):
    """
    Delivery/Shipment model.
    """

    DELIVERY_STATUS = [
        ("preparing", "准备中"),
        ("ready", "待发货"),
        ("partially_shipped", "部分发货"),
        ("shipped", "已发货"),
        ("in_transit", "运输中"),
        ("delivered", "已送达"),
        ("failed", "配送失败"),
        ("returned", "已退回"),
    ]

    # Delivery information
    delivery_number = models.CharField("发货单号", max_length=100, unique=True)
    sales_order = models.ForeignKey(
        SalesOrder, on_delete=models.CASCADE, related_name="deliveries", verbose_name="销售订单"
    )
    status = models.CharField("状态", max_length=20, choices=DELIVERY_STATUS, default="preparing")

    # Dates
    planned_date = models.DateField("计划发货日期")
    actual_date = models.DateField("实际发货日期", null=True, blank=True)
    delivered_date = models.DateField("送达日期", null=True, blank=True)

    # Shipping information
    shipping_address = models.TextField("收货地址")
    shipping_contact = models.CharField("收货联系人", max_length=100)
    shipping_phone = models.CharField("收货电话", max_length=20)
    shipping_method = models.CharField("配送方式", max_length=100, blank=True)
    carrier = models.CharField("承运商", max_length=100, blank=True)
    tracking_number = models.CharField("快递单号", max_length=100, blank=True)

    # Warehouse information
    warehouse = models.ForeignKey(
        "inventory.Warehouse", on_delete=models.CASCADE, verbose_name="发货仓库"
    )

    # Personnel
    prepared_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prepared_deliveries",
        verbose_name="备货人",
    )
    shipped_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="shipped_deliveries",
        verbose_name="发货人",
    )

    notes = models.TextField("备注", blank=True)

    class Meta:
        verbose_name = "发货单"
        verbose_name_plural = "发货单"
        db_table = "sales_delivery"
        ordering = ["-planned_date", "-created_at"]

    def __str__(self):
        return f"{self.delivery_number} - {self.sales_order.customer.name}"

    @property
    def total_planned_quantity(self):
        """总计划发货数量"""
        from decimal import Decimal

        return sum(item.quantity for item in self.items.all()) or Decimal("0")

    @property
    def total_shipped_quantity(self):
        """总实际发货数量"""
        from decimal import Decimal

        return sum(item.actual_shipped_quantity for item in self.items.all()) or Decimal("0")

    @property
    def total_unshipped_quantity(self):
        """总未发货数量"""
        return self.total_planned_quantity - self.total_shipped_quantity

    @property
    def is_fully_shipped(self):
        """是否全部发货完成"""
        return self.total_unshipped_quantity == 0 and self.total_planned_quantity > 0

    @property
    def is_partially_shipped(self):
        """是否部分发货"""
        return self.total_shipped_quantity > 0 and self.total_unshipped_quantity > 0


class DeliveryItem(BaseModel):
    """
    Delivery item model.
    """

    delivery = models.ForeignKey(
        Delivery, on_delete=models.CASCADE, related_name="items", verbose_name="发货单"
    )
    order_item = models.ForeignKey(SalesOrderItem, on_delete=models.CASCADE, verbose_name="订单明细")
    quantity = models.IntegerField("计划发货数量", help_text="计划发货数量")
    actual_shipped_quantity = models.IntegerField("实际发货数量", default=0, help_text="实际已发货数量（支持部分发货）")

    # Batch and serial information
    batch_number = models.CharField("批次号", max_length=100, blank=True)
    serial_numbers = models.TextField("序列号", blank=True, help_text="多个序列号用换行分隔")

    notes = models.TextField("备注", blank=True)

    class Meta:
        verbose_name = "发货明细"
        verbose_name_plural = "发货明细"
        db_table = "sales_delivery_item"

    def __str__(self):
        return f"{self.delivery.delivery_number} - {self.order_item.product.name}"

    @property
    def unshipped_quantity(self):
        """未发货数量"""
        return self.quantity - self.actual_shipped_quantity

    @property
    def is_fully_shipped(self):
        """是否已全部发货"""
        return self.actual_shipped_quantity >= self.quantity

    @property
    def is_partially_shipped(self):
        """是否部分发货"""
        return self.actual_shipped_quantity > 0 and self.actual_shipped_quantity < self.quantity


class SalesReturn(BaseModel):
    """
    Sales return model.
    """

    RETURN_STATUS = [
        ("pending", "待处理"),
        ("approved", "已批准"),
        ("received", "已收货"),
        ("processed", "已处理"),
        ("rejected", "已拒绝"),
    ]

    RETURN_REASONS = [
        ("defective", "产品缺陷"),
        ("wrong_item", "发错货"),
        ("damaged", "运输损坏"),
        ("not_needed", "不再需要"),
        ("other", "其他"),
    ]

    # Return information
    return_number = models.CharField("退货单号", max_length=100, unique=True)
    sales_order = models.ForeignKey(
        SalesOrder, on_delete=models.CASCADE, related_name="returns", verbose_name="原销售订单"
    )
    delivery = models.ForeignKey(
        Delivery, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="原发货单"
    )
    status = models.CharField("状态", max_length=20, choices=RETURN_STATUS, default="pending")
    reason = models.CharField("退货原因", max_length=20, choices=RETURN_REASONS)

    # Dates
    return_date = models.DateField("退货日期")
    received_date = models.DateField("收货日期", null=True, blank=True)

    # Financial information
    refund_amount = models.DecimalField("退款金额", max_digits=12, decimal_places=2, default=0)
    restocking_fee = models.DecimalField("重新入库费", max_digits=12, decimal_places=2, default=0)

    # Approval
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_returns",
        verbose_name="审核人",
    )
    approved_at = models.DateTimeField("审核时间", null=True, blank=True)

    notes = models.TextField("备注", blank=True)

    class Meta:
        verbose_name = "销售退货"
        verbose_name_plural = "销售退货"
        db_table = "sales_return"
        ordering = ["-return_date", "-created_at"]

    def __str__(self):
        return f"{self.return_number} - {self.sales_order.customer.name}"


class SalesReturnItem(BaseModel):
    """
    Sales return item model.
    """

    return_order = models.ForeignKey(
        SalesReturn, on_delete=models.CASCADE, related_name="items", verbose_name="退货单"
    )
    order_item = models.ForeignKey(SalesOrderItem, on_delete=models.CASCADE, verbose_name="原订单明细")
    quantity = models.DecimalField("退货数量", max_digits=12, decimal_places=4)
    unit_price = models.DecimalField("退货单价", max_digits=12, decimal_places=2)
    line_total = models.DecimalField("行总计", max_digits=12, decimal_places=2, default=0)

    # Quality information
    condition = models.CharField("货物状态", max_length=100, blank=True)
    disposition = models.CharField("处理方式", max_length=100, blank=True)

    # Batch and serial information
    batch_number = models.CharField("批次号", max_length=100, blank=True)
    serial_numbers = models.TextField("序列号", blank=True)

    notes = models.TextField("备注", blank=True)

    class Meta:
        verbose_name = "退货明细"
        verbose_name_plural = "退货明细"
        db_table = "sales_return_item"

    def __str__(self):
        return f"{self.return_order.return_number} - {self.order_item.product.name}"

    def save(self, *args, **kwargs):
        # 验证退货数量不能大于已交付数量，并且要考虑已有的退货数量
        if self.order_item:
            # 计算该订单项的总退货数量（不包括当前项，如果是更新的话）
            existing_return_quantity = 0
            if self.pk:  # 如果是更新现有项
                # 计算除当前项外的其他退货项数量
                existing_return_quantity = (
                    SalesReturnItem.objects.filter(
                        order_item=self.order_item, return_order__sales_order=self.order_item.order
                    )
                    .exclude(pk=self.pk)
                    .aggregate(total=models.Sum("quantity"))["total"]
                    or 0
                )
            else:  # 如果是新增项
                # 计算所有现有退货项数量
                existing_return_quantity = (
                    SalesReturnItem.objects.filter(
                        order_item=self.order_item, return_order__sales_order=self.order_item.order
                    ).aggregate(total=models.Sum("quantity"))["total"]
                    or 0
                )

            # 计算新的总退货数量
            new_total_return_quantity = existing_return_quantity + self.quantity

            # 检查是否超过已交付数量
            if new_total_return_quantity > self.order_item.delivered_quantity:
                available_return_quantity = (
                    self.order_item.delivered_quantity - existing_return_quantity
                )
                raise ValueError(
                    f"退货数量 ({self.quantity}) 加上已有退货数量 ({existing_return_quantity}) "
                    f"超过已交付数量 ({self.order_item.delivered_quantity})，"
                    f"最多可退数量为 ({available_return_quantity})"
                )

        # Calculate line total
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)


# ============================================
# 销售借用管理
# ============================================
class SalesLoan(BaseModel):
    """销售借用单 - 仅做系统记录"""

    LOAN_STATUS = [
        ("draft", "草稿"),
        ("loaned", "借出中"),
        ("partially_returned", "部分归还"),
        ("fully_returned", "全部归还"),
        ("converting", "转换中"),  # 转销售待审核
        ("converted", "已转销售"),
        ("cancelled", "已取消"),
    ]

    # 基本信息
    loan_number = models.CharField("借用单号", max_length=100, unique=True, db_index=True)
    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.CASCADE,
        related_name="sales_loans",
        verbose_name="客户",
    )
    salesperson = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sales_loans_as_salesperson",
        verbose_name="销售员",
    )

    # 状态管理
    status = models.CharField("状态", max_length=20, choices=LOAN_STATUS, default="draft")

    # 日期管理
    loan_date = models.DateField("借出日期")
    expected_return_date = models.DateField("预计归还日期", null=True, blank=True)

    # 借用信息
    purpose = models.TextField("借用目的", blank=True, help_text="样品试用/展会展示/客户测试等")
    delivery_address = models.TextField("借出地址", blank=True)
    contact_person = models.CharField("联系人", max_length=100, blank=True)
    contact_phone = models.CharField("联系电话", max_length=20, blank=True)

    # 转销售关联
    converted_order = models.ForeignKey(
        "SalesOrder",
        verbose_name="转换的销售订单",
        null=True,
        blank=True,
        related_name="source_loan",
        on_delete=models.SET_NULL,
    )

    # 转销售审核信息
    conversion_approved_by = models.ForeignKey(
        User,
        verbose_name="转销售审核人",
        null=True,
        blank=True,
        related_name="loan_conversion_approved",
        on_delete=models.SET_NULL,
    )
    conversion_approved_at = models.DateTimeField("转销售审核时间", null=True, blank=True)
    conversion_notes = models.TextField("转销售备注", blank=True)

    # 备注
    notes = models.TextField("备注", blank=True)

    class Meta:
        verbose_name = "销售借用单"
        verbose_name_plural = "销售借用单"
        db_table = "sales_loan"
        ordering = ["-loan_date", "-created_at"]

    def __str__(self):
        return f"{self.loan_number} - {self.customer.name}"

    # 计算属性
    @property
    def total_loaned_quantity(self):
        """总借出数量"""
        return sum(item.quantity for item in self.items.filter(is_deleted=False))

    @property
    def total_returned_quantity(self):
        """总归还数量"""
        return sum(item.returned_quantity for item in self.items.filter(is_deleted=False))

    @property
    def total_remaining_quantity(self):
        """总剩余数量（可转销售）"""
        return sum(item.remaining_quantity for item in self.items.filter(is_deleted=False))

    @property
    def is_fully_returned(self):
        """是否全部归还"""
        return self.total_remaining_quantity == 0


class SalesLoanItem(BaseModel):
    """销售借用明细"""

    loan = models.ForeignKey(
        SalesLoan, on_delete=models.CASCADE, related_name="items", verbose_name="借用单"
    )
    product = models.ForeignKey("products.Product", on_delete=models.CASCADE, verbose_name="产品")

    # 数量管理
    quantity = models.DecimalField("借出数量", max_digits=12, decimal_places=4, help_text="借给客户的数量")
    returned_quantity = models.DecimalField("已归还数量", max_digits=12, decimal_places=4, default=0)

    # 物料追踪
    batch_number = models.CharField("批次号", max_length=100, blank=True)
    serial_numbers = models.TextField("序列号", blank=True, help_text="多个序列号用换行分隔")

    # 转销售时的定价（手动输入）
    conversion_unit_price = models.DecimalField(
        "转销售单价", max_digits=10, decimal_places=2, null=True, blank=True, help_text="转销售时手动输入的含税单价"
    )
    conversion_quantity = models.DecimalField(
        "转销售数量", max_digits=12, decimal_places=4, default=0, help_text="已转销售的数量"
    )

    # 附加信息
    specifications = models.TextField("规格要求", blank=True)
    notes = models.TextField("备注", blank=True)

    class Meta:
        verbose_name = "销售借用明细"
        verbose_name_plural = "销售借用明细"
        db_table = "sales_loan_item"

    def __str__(self):
        return f"{self.loan.loan_number} - {self.product.name}"

    @property
    def remaining_quantity(self):
        """剩余未归还数量（可转销售）"""
        return self.quantity - self.returned_quantity - self.conversion_quantity

    @property
    def can_convert(self):
        """是否可转销售"""
        return self.remaining_quantity > 0
