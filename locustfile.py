"""
BetterLaser ERP - Locust性能测试配置
使用方法: locust -f locustfile.py --host=http://localhost:8000
"""

from locust import HttpUser, task, between, SequentialTaskSet
import json
import random


class SalesUserBehavior(SequentialTaskSet):
    """销售人员行为模拟"""

    def on_start(self):
        """登录"""
        response = self.client.post("/api/auth/login/", json={
            "username": "sales_user",
            "password": "testpass123"
        })
        if response.status_code == 200:
            self.token = response.json().get("token")
            self.client.headers.update({
                "Authorization": f"Bearer {self.token}"
            })

    @task
    def view_customer_list(self):
        """查看客户列表"""
        self.client.get("/api/customers/?page=1&page_size=20")

    @task
    def search_products(self):
        """搜索产品"""
        keywords = ["激光", "切割机", "雕刻机", "打标机"]
        keyword = random.choice(keywords)
        self.client.get(f"/api/products/?search={keyword}")

    @task
    def view_quote_list(self):
        """查看报价单列表"""
        self.client.get("/api/sales/quotes/?status=draft&page=1")

    @task
    def create_quote(self):
        """创建报价单"""
        data = {
            "customer": random.randint(1, 100),
            "quote_date": "2026-01-06",
            "valid_until": "2026-02-06",
            "items": [
                {
                    "product": random.randint(1, 50),
                    "quantity": random.randint(1, 10),
                    "unit_price": random.uniform(10000, 100000)
                }
            ]
        }
        self.client.post("/api/sales/quotes/", json=data)

    @task
    def view_order_list(self):
        """查看订单列表"""
        self.client.get("/api/sales/orders/?page=1&page_size=20")

    @task
    def view_order_detail(self):
        """查看订单详情"""
        order_id = random.randint(1, 1000)
        self.client.get(f"/api/sales/orders/{order_id}/")


class PurchaseUserBehavior(SequentialTaskSet):
    """采购人员行为模拟"""

    def on_start(self):
        """登录"""
        response = self.client.post("/api/auth/login/", json={
            "username": "purchase_user",
            "password": "testpass123"
        })
        if response.status_code == 200:
            self.token = response.json().get("token")
            self.client.headers.update({
                "Authorization": f"Bearer {self.token}"
            })

    @task
    def view_supplier_list(self):
        """查看供应商列表"""
        self.client.get("/api/suppliers/?page=1&page_size=20")

    @task
    def view_purchase_orders(self):
        """查看采购订单"""
        self.client.get("/api/purchase/orders/?page=1")

    @task
    def create_purchase_inquiry(self):
        """创建采购询价"""
        data = {
            "inquiry_date": "2026-01-06",
            "required_date": "2026-01-20",
            "items": [
                {
                    "product": random.randint(1, 50),
                    "quantity": random.randint(10, 100)
                }
            ],
            "suppliers": [random.randint(1, 50) for _ in range(3)]
        }
        self.client.post("/api/purchase/inquiries/", json=data)

    @task
    def view_quality_inspections(self):
        """查看质检记录"""
        self.client.get("/api/purchase/inspections/?page=1")


class WarehouseUserBehavior(SequentialTaskSet):
    """仓库管理员行为模拟"""

    def on_start(self):
        """登录"""
        response = self.client.post("/api/auth/login/", json={
            "username": "warehouse_user",
            "password": "testpass123"
        })
        if response.status_code == 200:
            self.token = response.json().get("token")
            self.client.headers.update({
                "Authorization": f"Bearer {self.token}"
            })

    @task(3)
    def view_inventory_stock(self):
        """查看库存（权重3）"""
        self.client.get("/api/inventory/stock/?warehouse=1")

    @task(2)
    def search_product_stock(self):
        """搜索产品库存（权重2）"""
        product_id = random.randint(1, 100)
        self.client.get(f"/api/inventory/stock/?product={product_id}")

    @task(1)
    def view_low_stock_alert(self):
        """查看低库存预警（权重1）"""
        self.client.get("/api/inventory/stock/?is_low_stock=true")

    @task(2)
    def view_inbound_orders(self):
        """查看入库单"""
        self.client.get("/api/inventory/inbound/?status=pending")

    @task(2)
    def view_outbound_orders(self):
        """查看出库单"""
        self.client.get("/api/inventory/outbound/?status=pending")

    @task(1)
    def view_inventory_transactions(self):
        """查看库存变动记录"""
        self.client.get("/api/inventory/transactions/?page=1")


class FinanceUserBehavior(SequentialTaskSet):
    """财务人员行为模拟"""

    def on_start(self):
        """登录"""
        response = self.client.post("/api/auth/login/", json={
            "username": "finance_user",
            "password": "testpass123"
        })
        if response.status_code == 200:
            self.token = response.json().get("token")
            self.client.headers.update({
                "Authorization": f"Bearer {self.token}"
            })

    @task(3)
    def view_customer_accounts(self):
        """查看应收账款（权重3）"""
        self.client.get("/api/finance/customer-accounts/?status=pending")

    @task(3)
    def view_supplier_accounts(self):
        """查看应付账款（权重3）"""
        self.client.get("/api/finance/supplier-accounts/?status=pending")

    @task(2)
    def view_payment_records(self):
        """查看收付款记录"""
        self.client.get("/api/finance/payments/?page=1")

    @task(1)
    def generate_financial_report(self):
        """生成财务报表（慢速操作）"""
        self.client.get("/api/finance/reports/?type=summary&date_from=2026-01-01&date_to=2026-01-31")

    @task(2)
    def view_invoices(self):
        """查看发票列表"""
        self.client.get("/api/finance/invoices/?page=1")


class SalesUser(HttpUser):
    """销售人员用户类"""
    tasks = [SalesUserBehavior]
    wait_time = between(1, 3)  # 每个任务间隔1-3秒
    weight = 3  # 权重，销售人员占30%


class PurchaseUser(HttpUser):
    """采购人员用户类"""
    tasks = [PurchaseUserBehavior]
    wait_time = between(2, 5)
    weight = 2  # 采购人员占20%


class WarehouseUser(HttpUser):
    """仓库管理员用户类"""
    tasks = [WarehouseUserBehavior]
    wait_time = between(1, 4)
    weight = 3  # 仓库人员占30%


class FinanceUser(HttpUser):
    """财务人员用户类"""
    tasks = [FinanceUserBehavior]
    wait_time = between(2, 5)
    weight = 2  # 财务人员占20%


# 简单的性能测试用户（用于快速测试）
class QuickTestUser(HttpUser):
    """快速测试用户"""
    wait_time = between(1, 2)

    def on_start(self):
        """登录"""
        response = self.client.post("/api/auth/login/", json={
            "username": "testuser",
            "password": "testpass123"
        })
        if response.status_code == 200:
            self.token = response.json().get("token")
            self.client.headers.update({
                "Authorization": f"Bearer {self.token}"
            })

    @task(5)
    def view_dashboard(self):
        """访问仪表板（权重5）"""
        self.client.get("/")

    @task(3)
    def list_orders(self):
        """订单列表（权重3）"""
        self.client.get("/api/sales/orders/")

    @task(2)
    def view_order(self):
        """查看订单（权重2）"""
        order_id = random.randint(1, 100)
        with self.client.get(f"/api/sales/orders/{order_id}/", catch_response=True) as response:
            if response.status_code == 404:
                response.success()  # 404是预期的，标记为成功

    @task(1)
    def list_products(self):
        """产品列表（权重1）"""
        self.client.get("/api/products/")
