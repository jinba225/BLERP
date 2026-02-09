"""
测试数据生成器
生成和管理测试数据
"""
import random
from datetime import datetime, timedelta
from decimal import Decimal

from django.core.management import call_command


class TestDataGenerator:
    """测试数据生成器"""

    @staticmethod
    def add_test_data():
        """添加测试数据"""
        try:
            # 简化实现：生成基础的测试数据
            # 实际实现应该根据模型结构生成具体的测试数据
            call_command("add_test_data", verbosity=0)
            return True, "测试数据添加成功"
        except Exception as e:
            return False, f"添加测试数据失败：{str(e)}"

    @staticmethod
    def generate_product_data(count=10):
        """生成产品测试数据"""
        products = []

        for i in range(count):
            product = {
                "code": f"TEST-{i + 1:04d}",
                "name": f"测试产品{i + 1}",
                "sku": f"TEST-{i + 1:04d}",
                "cost_price": Decimal(random.uniform(10, 100)),
                "stock": random.randint(10, 100),
                "status": random.choice(["active", "inactive"]),
            }
            products.append(product)

        return products

    @staticmethod
    def generate_customer_data(count=5):
        """生成客户测试数据"""
        customers = []

        for i in range(count):
            customer = {
                "code": f"CUST-{i + 1:04d}",
                "name": f"测试客户{i + 1}",
                "phone": f"1{random.randint(10000000000, 19999999999)}",
                "address": f"测试地址{i + 1}",
                "contact_person": f"测试联系人{i + 1}",
            }
            customers.append(customer)

        return customers

    @staticmethod
    def generate_order_data(count=5):
        """生成订单测试数据"""
        orders = []

        for i in range(count):
            order_date = datetime.now() - timedelta(days=random.randint(0, 30))
            order = {
                "order_number": f'ORD-{datetime.now().strftime("%Y%m%d")}-{i + 1:04d}',
                "customer_code": f"CUST-{random.randint(1, 5):04d}",
                "total_amount": Decimal(random.uniform(100, 1000)),
                "status": random.choice(["pending", "confirmed", "completed"]),
                "order_date": order_date,
            }
            orders.append(order)

        return orders

    @staticmethod
    def reset_auto_increment():
        """重置自增ID"""
        try:
            # SQLite重置自增ID
            call_command("reset_auto_increment", verbosity=0)
            return True, "自增ID重置成功"
        except Exception as e:
            return False, f"重置自增ID失败：{str(e)}"

    @staticmethod
    def clear_test_data():
        """清理测试数据"""
        try:
            call_command("clear_test_data", verbosity=0)
            return True, "测试数据清理成功"
        except Exception as e:
            return False, f"清理测试数据失败：{str(e)}"

    @staticmethod
    def get_test_data_statistics():
        """获取测试数据统计"""
        try:
            db_info = DatabaseManager.get_db_info()

            stats = {
                "database": db_info["name"],
                "products": 0,
                "customers": 0,
                "orders": 0,
                "total_size": db_info.get("size", 0),
            }

            return True, stats
        except Exception as e:
            return False, f"获取测试数据统计失败：{str(e)}"

    @staticmethod
    def seed_database():
        """填充数据库测试数据"""
        try:
            # 清理旧数据
            TestDataGenerator.clear_test_data()

            # 添加新数据
            TestDataGenerator.add_test_data()

            return True, "测试数据填充成功"
        except Exception as e:
            return False, f"测试数据填充失败：{str(e)}"
