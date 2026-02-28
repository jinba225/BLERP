"""
Inventory models for the ERP system.
"""
from core.models import BaseModel
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Warehouse(BaseModel):
    """
    Warehouse model.
    """

    WAREHOUSE_TYPES = [
        ("main", "主仓库"),
        ("branch", "分仓库"),
        ("virtual", "虚拟仓库"),
        ("transit", "在途仓库"),
        ("damaged", "残次品仓库"),
        ("borrow", "借用仓"),
    ]

    name = models.CharField("仓库名称", max_length=100)
    code = models.CharField("仓库编码", max_length=50, unique=True)
    warehouse_type = models.CharField(
        "仓库类型", max_length=20, choices=WAREHOUSE_TYPES, default="main"
    )
    address = models.TextField("仓库地址", blank=True)
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_warehouses",
        verbose_name="仓库管理员",
    )
    phone = models.CharField("联系电话", max_length=20, blank=True)
    capacity = models.DecimalField("仓库容量", max_digits=12, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField("是否启用", default=True)

    class Meta:
        verbose_name = "仓库"
        verbose_name_plural = "仓库"
        db_table = "inventory_warehouse"
        indexes = [
            models.Index(fields=["is_active"]),
            models.Index(fields=["warehouse_type", "is_active"]),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    @classmethod
    def get_main_warehouse(cls):
        """
        获取主仓库
        用于采购订单的默认收货仓库

        Returns:
            Warehouse: 主仓库对象

        Raises:
            Warehouse.DoesNotExist: 如果主仓库不存在
        """
        return cls.objects.get(warehouse_type="main", is_active=True, is_deleted=False)

    @classmethod
    def get_borrow_warehouse(cls):
        """
        获取借用仓
        用于采购借用和销售借用的出入库操作

        Returns:
            Warehouse: 借用仓对象

        Raises:
            Warehouse.DoesNotExist: 如果借用仓不存在
        """
        return cls.objects.get(warehouse_type="borrow", is_active=True, is_deleted=False)

    @property
    def current_utilization(self):
        """Calculate current warehouse utilization."""
        if not self.capacity:
            return 0
        total_volume = sum(
            [stock.quantity * (stock.product.volume or 0) for stock in self.stocks.all()]
        )
        return (total_volume / self.capacity) * 100 if self.capacity > 0 else 0


class Location(BaseModel):
    """
    Storage location model within warehouse.
    """

    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.CASCADE, related_name="locations", verbose_name="仓库"
    )
    code = models.CharField("库位编码", max_length=50)
    name = models.CharField("库位名称", max_length=100)
    aisle = models.CharField("通道", max_length=20, blank=True)
    shelf = models.CharField("货架", max_length=20, blank=True)
    level = models.CharField("层级", max_length=20, blank=True)
    position = models.CharField("位置", max_length=20, blank=True)
    capacity = models.DecimalField("容量", max_digits=12, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField("是否启用", default=True)

    class Meta:
        verbose_name = "库位"
        verbose_name_plural = "库位"
        db_table = "inventory_location"
        unique_together = ["warehouse", "code"]

    def __str__(self):
        return f"{self.warehouse.code}-{self.code}"


class InventoryStock(BaseModel):
    """
    Inventory stock model.
    """

    product = models.ForeignKey(
        "products.Product", on_delete=models.CASCADE, related_name="stocks", verbose_name="产品"
    )
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.CASCADE, related_name="stocks", verbose_name="仓库"
    )
    location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="库位"
    )
    quantity = models.IntegerField("库存数量", default=0)
    reserved_quantity = models.IntegerField("预留数量", default=0)
    cost_price = models.DecimalField("成本价", max_digits=12, decimal_places=2, default=0)
    is_low_stock_flag = models.BooleanField(
        "是否低库存", db_index=True, default=False, help_text="冗余字段，用于优化查询性能"
    )
    last_in_date = models.DateTimeField("最后入库时间", null=True, blank=True)
    last_out_date = models.DateTimeField("最后出库时间", null=True, blank=True)

    class Meta:
        verbose_name = "库存"
        verbose_name_plural = "库存"
        db_table = "inventory_stock"
        unique_together = ["product", "warehouse", "location"]
        indexes = [
            models.Index(fields=["warehouse", "product"]),
            models.Index(fields=["warehouse", "is_low_stock_flag"]),
            models.Index(fields=["location"]),
            models.Index(fields=["last_in_date"]),
            models.Index(fields=["last_out_date"]),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.warehouse.name} - {self.quantity}"

    @property
    def available_quantity(self):
        """Calculate available quantity (total - reserved)."""
        return self.quantity - self.reserved_quantity

    @property
    def is_low_stock(self):
        """Check if stock is below minimum level."""
        return self.quantity <= self.product.min_stock


class InventoryTransaction(BaseModel):
    """
    Inventory transaction model for tracking all stock movements.
    """

    TRANSACTION_TYPES = [
        ("in", "入库"),
        ("out", "出库"),
        ("transfer", "调拨"),
        ("adjustment", "调整"),
        ("return", "退货"),
        ("scrap", "报废"),
    ]

    REFERENCE_TYPES = [
        ("purchase_order", "采购订单"),
        ("sales_order", "销售订单"),
        ("production_order", "生产订单"),
        ("transfer_order", "调拨单"),
        ("adjustment", "库存调整"),
        ("return", "退货单"),
        ("manual", "手工录入"),
    ]

    transaction_type = models.CharField("交易类型", max_length=20, choices=TRANSACTION_TYPES)
    product = models.ForeignKey(
        "products.Product", on_delete=models.CASCADE, related_name="transactions", verbose_name="产品"
    )
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, verbose_name="仓库")
    location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="库位"
    )
    quantity = models.IntegerField("数量")
    unit_cost = models.DecimalField("单位成本", max_digits=12, decimal_places=2, default=0)
    total_cost = models.DecimalField("总成本", max_digits=12, decimal_places=2, default=0)

    # Reference information
    reference_type = models.CharField("关联类型", max_length=20, choices=REFERENCE_TYPES, blank=True)
    reference_id = models.CharField("关联单据ID", max_length=100, blank=True)
    reference_number = models.CharField("关联单据号", max_length=100, blank=True)

    # Batch and serial information
    batch_number = models.CharField("批次号", max_length=100, blank=True)
    serial_number = models.CharField("序列号", max_length=100, blank=True)
    expiry_date = models.DateField("过期日期", null=True, blank=True)

    # Transaction details
    transaction_date = models.DateTimeField("交易时间", auto_now_add=True)
    operator = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="操作员"
    )
    notes = models.TextField("备注", blank=True)

    class Meta:
        verbose_name = "库存交易"
        verbose_name_plural = "库存交易"
        db_table = "inventory_transaction"
        ordering = ["-transaction_date"]
        indexes = [
            models.Index(fields=["transaction_type", "warehouse"]),
            models.Index(fields=["product", "warehouse"]),
            models.Index(fields=["reference_type", "reference_id"]),
            models.Index(fields=["batch_number"]),
            models.Index(fields=["-transaction_date"]),
        ]

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.product.name} - {self.quantity}"

    def save(self, *args, **kwargs):
        # Calculate total cost
        self.total_cost = self.quantity * self.unit_cost
        super().save(*args, **kwargs)

        # Update stock levels
        self.update_stock()

    def update_stock(self):
        """Update stock levels based on transaction."""
        stock, created = InventoryStock.objects.get_or_create(
            product=self.product,
            warehouse=self.warehouse,
            location=self.location,
            defaults={"quantity": 0},
        )

        if self.transaction_type in ["in", "return"]:
            # 入库和退货：数量增加（使用绝对值确保正确）
            stock.quantity += abs(self.quantity)
            stock.last_in_date = self.transaction_date
        elif self.transaction_type in ["out", "scrap"]:
            # 出库和报废：数量减少（使用绝对值确保正确）
            stock.quantity -= abs(self.quantity)
            stock.last_out_date = self.transaction_date
        elif self.transaction_type == "adjustment":
            # 调整：quantity可以是正数（增加）或负数（减少）
            stock.quantity += self.quantity

        stock.save()


class StockAdjustment(BaseModel):
    """
    Stock adjustment model for inventory corrections.
    """

    ADJUSTMENT_TYPES = [
        ("increase", "增加"),
        ("decrease", "减少"),
        ("correction", "纠正"),
    ]

    ADJUSTMENT_REASONS = [
        ("count_error", "盘点差异"),
        ("damage", "损坏"),
        ("theft", "丢失"),
        ("expiry", "过期"),
        ("system_error", "系统错误"),
        ("other", "其他"),
    ]

    adjustment_number = models.CharField("调整单号", max_length=100, unique=True)
    adjustment_type = models.CharField("调整类型", max_length=20, choices=ADJUSTMENT_TYPES)
    reason = models.CharField("调整原因", max_length=20, choices=ADJUSTMENT_REASONS)
    product = models.ForeignKey("products.Product", on_delete=models.CASCADE, verbose_name="产品")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, verbose_name="仓库")
    location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="库位"
    )

    # Quantities
    original_quantity = models.IntegerField("原数量")
    adjusted_quantity = models.IntegerField("调整后数量")
    difference = models.IntegerField("差异数量", default=0)

    # Approval
    is_approved = models.BooleanField("是否审核", default=False)
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_adjustments",
        verbose_name="审核人",
    )
    approved_at = models.DateTimeField("审核时间", null=True, blank=True)

    notes = models.TextField("备注", blank=True)

    class Meta:
        verbose_name = "库存调整"
        verbose_name_plural = "库存调整"
        db_table = "inventory_adjustment"

    def __str__(self):
        return f"{self.adjustment_number} - {self.product.name}"

    def save(self, *args, **kwargs):
        # Calculate difference
        self.difference = self.adjusted_quantity - self.original_quantity
        super().save(*args, **kwargs)


class StockTransfer(BaseModel):
    """
    Stock transfer model for moving inventory between warehouses.
    """

    TRANSFER_STATUS = [
        ("draft", "草稿"),
        ("pending", "待审核"),
        ("approved", "已审核"),
        ("in_transit", "在途"),
        ("completed", "已完成"),
        ("cancelled", "已取消"),
    ]

    transfer_number = models.CharField("调拨单号", max_length=100, unique=True)
    from_warehouse = models.ForeignKey(
        Warehouse, on_delete=models.CASCADE, related_name="transfers_out", verbose_name="源仓库"
    )
    to_warehouse = models.ForeignKey(
        Warehouse, on_delete=models.CASCADE, related_name="transfers_in", verbose_name="目标仓库"
    )
    status = models.CharField("状态", max_length=20, choices=TRANSFER_STATUS, default="draft")
    transfer_date = models.DateField("调拨日期")
    expected_arrival_date = models.DateField("预计到达日期", null=True, blank=True)
    actual_arrival_date = models.DateField("实际到达日期", null=True, blank=True)

    # Approval
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_transfers",
        verbose_name="审核人",
    )
    approved_at = models.DateTimeField("审核时间", null=True, blank=True)

    notes = models.TextField("备注", blank=True)

    # 系统自动生成标识
    is_auto_generated = models.BooleanField(
        "系统自动生成", default=False, help_text="标识该调拨单是否由系统自动生成（如借用转采购）。系统生成的调拨单不允许编辑和反审核。"
    )

    class Meta:
        verbose_name = "库存调拨"
        verbose_name_plural = "库存调拨"
        db_table = "inventory_transfer"

    def __str__(self):
        return f"{self.transfer_number} - {self.from_warehouse.name} → {self.to_warehouse.name}"


class StockTransferItem(BaseModel):
    """
    Stock transfer item model.
    """

    transfer = models.ForeignKey(
        StockTransfer, on_delete=models.CASCADE, related_name="items", verbose_name="调拨单"
    )
    product = models.ForeignKey("products.Product", on_delete=models.CASCADE, verbose_name="产品")
    requested_quantity = models.IntegerField("申请数量")
    shipped_quantity = models.IntegerField("发货数量", default=0)
    received_quantity = models.IntegerField("收货数量", default=0)
    unit_cost = models.DecimalField("单位成本", max_digits=12, decimal_places=2, default=0)

    # Batch information
    batch_number = models.CharField("批次号", max_length=100, blank=True)
    expiry_date = models.DateField("过期日期", null=True, blank=True)

    notes = models.TextField("备注", blank=True)

    class Meta:
        verbose_name = "调拨明细"
        verbose_name_plural = "调拨明细"
        db_table = "inventory_transfer_item"

    def __str__(self):
        return f"{self.transfer.transfer_number} - {self.product.name}"


class StockCount(BaseModel):
    """
    Stock count/cycle count model.
    """

    COUNT_TYPES = [
        ("full", "全盘"),
        ("cycle", "循环盘点"),
        ("spot", "抽盘"),
    ]

    COUNT_STATUS = [
        ("planned", "计划中"),
        ("in_progress", "进行中"),
        ("completed", "已完成"),
        ("cancelled", "已取消"),
    ]

    count_number = models.CharField("盘点单号", max_length=100, unique=True)
    count_type = models.CharField("盘点类型", max_length=20, choices=COUNT_TYPES)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, verbose_name="仓库")
    status = models.CharField("状态", max_length=20, choices=COUNT_STATUS, default="planned")
    planned_date = models.DateField("计划日期")
    start_date = models.DateTimeField("开始时间", null=True, blank=True)
    end_date = models.DateTimeField("结束时间", null=True, blank=True)

    # Personnel
    supervisor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="supervised_counts",
        verbose_name="盘点主管",
    )
    counters = models.ManyToManyField(
        User, blank=True, related_name="stock_counts", verbose_name="盘点员"
    )

    notes = models.TextField("备注", blank=True)

    class Meta:
        verbose_name = "库存盘点"
        verbose_name_plural = "库存盘点"
        db_table = "inventory_count"

    def __str__(self):
        return f"{self.count_number} - {self.warehouse.name}"


class StockCountItem(BaseModel):
    """
    Stock count item model.
    """

    count = models.ForeignKey(
        StockCount, on_delete=models.CASCADE, related_name="items", verbose_name="盘点单"
    )
    product = models.ForeignKey("products.Product", on_delete=models.CASCADE, verbose_name="产品")
    location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="库位"
    )
    system_quantity = models.IntegerField("系统数量")
    counted_quantity = models.IntegerField("盘点数量", null=True, blank=True)
    difference = models.IntegerField("差异数量", default=0)

    # Batch information
    batch_number = models.CharField("批次号", max_length=100, blank=True)
    expiry_date = models.DateField("过期日期", null=True, blank=True)

    # Count details
    counter = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="盘点员"
    )
    count_time = models.DateTimeField("盘点时间", null=True, blank=True)
    notes = models.TextField("备注", blank=True)

    class Meta:
        verbose_name = "盘点明细"
        verbose_name_plural = "盘点明细"
        db_table = "inventory_count_item"

    def __str__(self):
        return f"{self.count.count_number} - {self.product.name}"

    def save(self, *args, **kwargs):
        # Calculate difference
        if self.counted_quantity is not None:
            self.difference = self.counted_quantity - self.system_quantity
        super().save(*args, **kwargs)


class InboundOrder(BaseModel):
    """
    Inbound order model (independent goods receipt).
    """

    ORDER_TYPES = [
        ("purchase", "采购入库"),
        ("sales_return", "销售退货入库"),
        ("transfer", "调拨入库"),
        ("other", "其他入库"),
    ]

    ORDER_STATUS = [
        ("draft", "草稿"),
        ("pending", "待审核"),
        ("approved", "已审核"),
        ("completed", "已完成"),
        ("cancelled", "已取消"),
    ]

    order_number = models.CharField("入库单号", max_length=100, unique=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, verbose_name="仓库")
    order_type = models.CharField("入库类型", max_length=20, choices=ORDER_TYPES)
    status = models.CharField("状态", max_length=20, choices=ORDER_STATUS, default="draft")
    order_date = models.DateField("入库日期")

    # Optional supplier reference
    supplier = models.ForeignKey(
        "suppliers.Supplier", on_delete=models.SET_NULL, null=True, blank=True, verbose_name="供应商"
    )

    # Reference information
    reference_number = models.CharField("参考单号", max_length=100, blank=True)
    reference_type = models.CharField("参考类型", max_length=50, blank=True)
    reference_id = models.IntegerField("参考ID", null=True, blank=True)

    # Approval
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_inbound_orders",
        verbose_name="审核人",
    )
    approved_at = models.DateTimeField("审核时间", null=True, blank=True)

    notes = models.TextField("备注", blank=True)

    class Meta:
        verbose_name = "入库单"
        verbose_name_plural = "入库单"
        db_table = "inventory_inbound_order"
        ordering = ["-order_date", "-created_at"]

    def clean(self):
        """模型验证"""
        from django.core.exceptions import ValidationError

        # 如果是"其他入库",必须填写备注
        if self.order_type == "other" and not self.notes:
            raise ValidationError({"notes": "其他入库必须填写备注说明原因"})

    def save(self, *args, **kwargs):
        self.clean()  # 调用验证
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_number} - {self.warehouse.name}"


class InboundOrderItem(BaseModel):
    """
    Inbound order item model.
    """

    inbound_order = models.ForeignKey(
        InboundOrder, on_delete=models.CASCADE, related_name="items", verbose_name="入库单"
    )
    product = models.ForeignKey("products.Product", on_delete=models.CASCADE, verbose_name="产品")
    location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="库位"
    )
    quantity = models.IntegerField("入库数量")
    batch_number = models.CharField("批次号", max_length=100, blank=True)
    expiry_date = models.DateField("过期日期", null=True, blank=True)
    notes = models.TextField("备注", blank=True)

    class Meta:
        verbose_name = "入库明细"
        verbose_name_plural = "入库明细"
        db_table = "inventory_inbound_order_item"

    def __str__(self):
        return f"{self.inbound_order.order_number} - {self.product.name}"


class OutboundOrder(BaseModel):
    """
    Outbound order model (independent goods issue).
    """

    ORDER_TYPES = [
        ("sales", "销售出库"),
        ("purchase_return", "采购退货出库"),
        ("production", "生产出库"),
        ("transfer", "调拨出库"),
        ("other", "其他出库"),
    ]

    ORDER_STATUS = [
        ("draft", "草稿"),
        ("pending", "待审核"),
        ("approved", "已审核"),
        ("completed", "已完成"),
        ("cancelled", "已取消"),
    ]

    order_number = models.CharField("出库单号", max_length=100, unique=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, verbose_name="仓库")
    order_type = models.CharField("出库类型", max_length=20, choices=ORDER_TYPES)
    status = models.CharField("状态", max_length=20, choices=ORDER_STATUS, default="draft")
    order_date = models.DateField("出库日期")

    # Optional customer reference
    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.SET_NULL, null=True, blank=True, verbose_name="客户"
    )

    # Reference information
    reference_number = models.CharField("参考单号", max_length=100, blank=True)
    reference_type = models.CharField("参考类型", max_length=50, blank=True)
    reference_id = models.IntegerField("参考ID", null=True, blank=True)

    # Approval
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_outbound_orders",
        verbose_name="审核人",
    )
    approved_at = models.DateTimeField("审核时间", null=True, blank=True)

    notes = models.TextField("备注", blank=True)

    class Meta:
        verbose_name = "出库单"
        verbose_name_plural = "出库单"
        db_table = "inventory_outbound_order"
        ordering = ["-order_date", "-created_at"]

    def clean(self):
        """模型验证"""
        from django.core.exceptions import ValidationError

        # 如果是"其他出库",必须填写备注
        if self.order_type == "other" and not self.notes:
            raise ValidationError({"notes": "其他出库必须填写备注说明原因"})

    def save(self, *args, **kwargs):
        self.clean()  # 调用验证
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_number} - {self.warehouse.name}"


class OutboundOrderItem(BaseModel):
    """
    Outbound order item model.
    """

    outbound_order = models.ForeignKey(
        OutboundOrder, on_delete=models.CASCADE, related_name="items", verbose_name="出库单"
    )
    product = models.ForeignKey("products.Product", on_delete=models.CASCADE, verbose_name="产品")
    location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="库位"
    )
    quantity = models.DecimalField("出库数量", max_digits=12, decimal_places=4)
    batch_number = models.CharField("批次号", max_length=100, blank=True)
    notes = models.TextField("备注", blank=True)

    class Meta:
        verbose_name = "出库明细"
        verbose_name_plural = "出库明细"
        db_table = "inventory_outbound_order_item"

    def __str__(self):
        return f"{self.outbound_order.order_number} - {self.product.name}"
