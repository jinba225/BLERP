"""
Django ERP Locust性能测试脚本

用法:
  # 开发环境测试
  locust -f locustfile.py --host=http://localhost:8000

  # 生产环境测试（小心！）
  locust -f locustfile.py --host=https://your-domain.com --users=100 --spawn-rate=10

  # 无头模式（命令行）
  locust -f locustfile.py --host=http://localhost:8000 --headless --users=50 --spawn-rate=5 --run-time=1m
"""

from locust import HttpUser, task, between, events
from locust.runners import MasterRunner
import time
import random


class ERPUserBehavior(HttpUser):
    """
    ERP用户行为模拟
    
    模拟真实用户在ERP系统中的常见操作:
    1. 登录系统
    2. 查看仪表盘
    3. 浏览列表页
    4. 查看详情页
    5. 执行搜索
    """
    
    # 等待时间: 1-3秒之间（模拟真实用户思考时间）
    wait_time = between(1, 3)
    
    def on_start(self):
        """用户开始时执行（登录）"""
        self.login()
    
    def login(self):
        """登录系统"""
        # 注意：这需要创建一个测试用户或使用已存在的用户
        # 实际使用时需要替换为有效的凭证
        self.client.post("/login/", data={
            "username": "test_user",
            "password": "test_password"
        })
    
    @task(3)
    def view_dashboard(self):
        """查看仪表盘（高权重，最常用）"""
        self.client.get("/")
        self.client.get("/api/dashboard/stats/")
    
    @task(2)
    def view_sales_orders(self):
        """查看销售订单列表"""
        self.client.get("/sales/orders/")
        self.client.get("/api/sales/orders/")
    
    @task(2)
    def view_purchase_orders(self):
        """查看采购订单列表"""
        self.client.get("/purchase/orders/")
        self.client.get("/api/purchase/orders/")
    
    @task(1)
    def view_inventory(self):
        """查看库存列表"""
        self.client.get("/inventory/stocks/")
        self.client.get("/api/inventory/stocks/")
    
    @task(1)
    def view_customers(self):
        """查看客户列表"""
        self.client.get("/customers/")
        self.client.get("/api/customers/")
    
    @task(1)
    def view_suppliers(self):
        """查看供应商列表"""
        self.client.get("/suppliers/")
        self.client.get("/api/suppliers/")
    
    @task(1)
    def view_finance_reports(self):
        """查看财务报表"""
        self.client.get("/finance/dashboard/")
        self.client.get("/api/finance/reports/balance-sheet/")
    
    @task(2)
    def search(self):
        """执行搜索（常见操作）"""
        search_terms = ["订单", "产品", "客户", "供应商", "库存"]
        term = random.choice(search_terms)
        self.client.get(f"/search/?q={term}")
    
    @task(1)
    def view_order_detail(self):
        """查看订单详情"""
        # 随机查看不同类型的订单详情
        order_types = ["sales", "purchase"]
        order_type = random.choice(order_types)
        order_id = random.randint(1, 100)
        self.client.get(f"/{order_type}/orders/{order_id}/")


class AdminUserBehavior(HttpUser):
    """
    管理员用户行为
    
    模拟管理员的操作:
    1. 登录后台
    2. 查看管理列表
    3. 创建/编辑记录
    """
    
    wait_time = between(2, 5)
    
    def on_start(self):
        """管理员登录（使用超级用户）"""
        # 使用Django admin登录
        self.client.post("/admin/login/", data={
            "username": "admin",
            "password": "admin123"
        })
    
    @task(3)
    def view_admin_index(self):
        """查看Admin首页"""
        self.client.get("/admin/")
    
    @task(2)
    def view_sales_orders(self):
        """查看销售订单管理"""
        self.client.get("/admin/sales/salesorder/")
    
    @task(2)
    def view_purchase_orders(self):
        """查看采购订单管理"""
        self.client.get("/admin/purchase/purchaseorder/")
    
    @task(1)
    def view_products(self):
        """查看产品管理"""
        self.client.get("/admin/products/product/")
    
    @task(1)
    def view_customers(self):
        """查看客户管理"""
        self.client.get("/admin/customers/customer/")
    
    @task(1)
    def create_order(self):
        """创建订单（GET表单）"""
        self.client.get("/admin/sales/salesorder/add/")
    
    @task(1)
    def view_users(self):
        """查看用户管理"""
        self.client.get("/admin/users/user/")


class APIUserBehavior(HttpUser):
    """
    API用户行为
    
    模拟纯API客户端（移动应用、第三方集成）:
    1. API认证
    2. 调用API端点
    3. 高频请求
    """
    
    wait_time = between(0.5, 2)  # API客户端等待时间更短
    
    def on_start(self):
        """获取API Token"""
        # 使用JWT获取token
        response = self.client.post("/api/auth/login/", json={
            "username": "api_user",
            "password": "api_password"
        })
        
        if response.status_code == 200:
            try:
                data = response.json()
                self.token = data.get("token", "")
                self.headers = {"Authorization": f"Bearer {self.token}"}
            except:
                self.token = ""
                self.headers = {}
        else:
            self.token = ""
            self.headers = {}
    
    @task(5)
    def get_products(self):
        """获取产品列表（高频）"""
        if self.headers:
            self.client.get("/api/products/", headers=self.headers)
    
    @task(3)
    def get_orders(self):
        """获取订单列表"""
        if self.headers:
            self.client.get("/api/sales/orders/", headers=self.headers)
    
    @task(2)
    def get_inventory(self):
        """获取库存信息"""
        if self.headers:
            self.client.get("/api/inventory/stocks/", headers=self.headers)
    
    @task(1)
    def create_order(self):
        """创建订单（POST请求）"""
        if self.headers:
            self.client.post("/api/sales/orders/", 
                headers=self.headers,
                json={
                    "customer": 1,
                    "items": [{"product": 1, "quantity": 10}]
                }
            )


# ============================================
# 性能指标事件处理器
# ============================================

@events.request.add_listener
def on_request(request_type, name, response_time, response_length, **kwargs):
    """
    请求完成事件
    
    可以在这里记录自定义指标或发送到监控系统
    """
    if response_time > 2000:  # 响应时间超过2秒
        print(f"⚠️  慢请求: {name} - {response_time}ms")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """
    测试结束事件
    
    输出性能报告摘要
    """
    if environment.stats.total.fail_ratio > 0.05:  # 失败率超过5%
        print("\n⚠️  警告: 测试失败率过高！")
        print(f"   失败率: {environment.stats.total.fail_ratio:.2%}")
    
    if environment.stats.total.avg_response_time > 1000:  # 平均响应时间超过1秒
        print("\n⚠️  警告: 平均响应时间过长！")
        print(f"   平均响应时间: {environment.stats.total.avg_response_time:.0f}ms")
    
    print("\n📊 性能测试完成！")
    print(f"   总请求数: {environment.stats.total.num_requests}")
    print(f"   失败率: {environment.stats.total.fail_ratio:.2%}")
    print(f"   平均响应时间: {environment.stats.total.avg_response_time:.0f}ms")
    print(f"   中位数响应时间: {environment.stats.total.median_response_time:.0f}ms")


# ============================================
# 性能测试场景配置
# ============================================

class QuickTestUser(HttpUser):
    """
    快速测试用户（用于快速验证）
    
    只访问最关键的页面
    """
    wait_time = between(1, 2)
    
    @task
    def view_homepage(self):
        """只访问首页"""
        self.client.get("/")


# ============================================
# 使用建议
# ============================================

"""
性能测试场景建议:

1. 开发环境验证:
   locust -f locustfile.py --host=http://localhost:8000 \
         --users=10 --spawn-rate=1

2. 负载测试（中等负载）:
   locust -f locustfile.py --host=http://staging.example.com \
         --users=50 --spawn-rate=5 --run-time=5m

3. 压力测试（高负载）:
   locust -f locustfile.py --host=http://staging.example.com \
         --users=200 --spawn-rate=20 --run-time=10m

4. 峰值测试（模拟突发流量）:
   locust -f locustfile.py --host=http://staging.example.com \
         --users=500 --spawn-rate=50 --run-time=2m

5. 稳定性测试（长时间）:
   locust -f locustfile.py --host=http://staging.example.com \
         --users=100 --spawn-rate=10 --run-time=1h

性能目标:
- ✅ 平均响应时间 < 500ms
- ✅ 95%请求响应时间 < 1s
- ✅ 错误率 < 1%
- ✅ 支持100并发用户
"""
