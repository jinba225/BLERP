"""
Customers模块 - API测试
测试 api_get_customer_contacts 等自定义API端点
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
import json

from apps.customers.models import Customer, CustomerContact, CustomerCategory
from apps.departments.models import Department

User = get_user_model()


class CustomersAPITestCase(TestCase):
    """Customers API测试基类 - 准备测试数据"""

    def setUp(self):
        """测试前准备 - 创建测试用户和客户数据"""
        # 创建部门
        self.department = Department.objects.create(
            name='销售部',
            code='SALES',
        )

        # 创建测试用户
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com',
            employee_id='EMP001',
            department=self.department,
        )

        # 创建客户分类
        self.category = CustomerCategory.objects.create(
            name='重要客户',
            code='VIP',
            discount_rate=0.95,
            created_by=self.user
        )

        # 创建测试客户
        self.customer1 = Customer.objects.create(
            name='测试客户1',
            code='C001',
            customer_level='A',
            status='active',
            category=self.category,
            website='https://customer1.example.com',
            created_by=self.user
        )

        self.customer2 = Customer.objects.create(
            name='测试客户2',
            code='C002',
            customer_level='B',
            status='active',
            created_by=self.user
        )

        # 创建客户联系人
        self.contact1 = CustomerContact.objects.create(
            customer=self.customer1,
            name='张三',
            position='采购经理',
            department='采购部',
            phone='010-11111111',
            mobile='13800138001',
            email='zhangsan@customer1.com',
            is_primary=True,
            created_by=self.user
        )

        self.contact2 = CustomerContact.objects.create(
            customer=self.customer1,
            name='李四',
            position='技术总监',
            department='技术部',
            phone='010-22222222',
            mobile='13800138002',
            email='lisi@customer1.com',
            is_primary=False,
            created_by=self.user
        )

        self.contact3 = CustomerContact.objects.create(
            customer=self.customer2,
            name='王五',
            position='老板',
            phone='010-33333333',
            mobile='13800138003',
            created_by=self.user
        )

        # 创建客户端并登录
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')


class CustomerContactsAPITestCase(CustomersAPITestCase):
    """客户联系人API测试"""

    def test_get_customer_contacts_success(self):
        """测试成功获取客户联系人列表"""
        url = reverse('customers:api_customer_contacts', args=[self.customer1.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # 验证响应结构
        self.assertTrue(data['success'])
        self.assertIn('contacts', data)

        # 验证联系人数据
        contacts = data['contacts']
        self.assertEqual(len(contacts), 2)  # customer1有2个联系人

        # 验证联系人字段
        contact_names = [c['name'] for c in contacts]
        self.assertIn('张三', contact_names)
        self.assertIn('李四', contact_names)

        # 验证第一个联系人的详细信息（按name排序）
        first_contact = contacts[0]
        self.assertIn('id', first_contact)
        self.assertIn('name', first_contact)
        self.assertIn('position', first_contact)
        self.assertIn('department', first_contact)
        self.assertIn('phone', first_contact)
        self.assertIn('mobile', first_contact)
        self.assertIn('email', first_contact)
        self.assertIn('notes', first_contact)

    def test_get_customer_contacts_ordering(self):
        """测试联系人按名称排序"""
        url = reverse('customers:api_customer_contacts', args=[self.customer1.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        contacts = data['contacts']

        # 验证按name排序
        names = [c['name'] for c in contacts]
        self.assertEqual(names, sorted(names))

    def test_get_customer_contacts_customer_not_found(self):
        """测试客户不存在的情况"""
        url = reverse('customers:api_customer_contacts', args=[99999])
        response = self.client.get(url)

        # API返回500状态码（而不是404）
        self.assertEqual(response.status_code, 500)
        data = response.json()

        # 验证响应结构
        self.assertFalse(data['success'])
        self.assertIn('error', data)

    def test_get_customer_contacts_soft_deleted_customer(self):
        """测试已删除的客户（软删除）"""
        self.customer1.delete()  # 软删除

        url = reverse('customers:api_customer_contacts', args=[self.customer1.pk])
        response = self.client.get(url)

        # API返回500状态码（而不是404）
        self.assertEqual(response.status_code, 500)
        data = response.json()

        # 验证响应结构
        self.assertFalse(data['success'])
        self.assertIn('error', data)

    def test_get_customer_contacts_excludes_soft_deleted_contacts(self):
        """测试排除已删除的联系人"""
        # 软删除一个联系人
        self.contact1.delete()

        url = reverse('customers:api_customer_contacts', args=[self.customer1.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        contacts = data['contacts']

        # 应该只返回1个联系人（李四）
        self.assertEqual(len(contacts), 1)
        self.assertEqual(contacts[0]['name'], '李四')

    def test_get_customer_contacts_empty_list(self):
        """测试客户没有联系人的情况"""
        # 删除customer1的所有联系人
        self.contact1.delete()
        self.contact2.delete()

        url = reverse('customers:api_customer_contacts', args=[self.customer1.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertTrue(data['success'])
        self.assertEqual(len(data['contacts']), 0)

    def test_get_customer_contacts_unauthenticated(self):
        """测试未认证用户访问（如果需要登录）"""
        # 退出登录
        self.client.logout()

        url = reverse('customers:api_customer_contacts', args=[self.customer1.pk])
        response = self.client.get(url)

        # 如果API需要登录，应该返回302重定向或403
        # 这里假设需要登录
        self.assertIn(response.status_code, [302, 403])

    def test_get_customer_contacts_response_format(self):
        """测试响应格式的完整性"""
        url = reverse('customers:api_customer_contacts', args=[self.customer1.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

        data = response.json()

        # 验证必需字段
        self.assertIsInstance(data['success'], bool)
        self.assertIsInstance(data['contacts'], list)

        # 验证联系人字段完整性
        if len(data['contacts']) > 0:
            contact = data['contacts'][0]
            required_fields = ['id', 'name', 'position', 'department',
                             'phone', 'mobile', 'email', 'notes']
            for field in required_fields:
                self.assertIn(field, contact)

    def test_get_customer_contacts_different_customers(self):
        """测试不同客户返回不同的联系人"""
        # Customer1 有2个联系人
        url1 = reverse('customers:api_customer_contacts', args=[self.customer1.pk])
        response1 = self.client.get(url1)
        data1 = response1.json()

        # Customer2 有1个联系人
        url2 = reverse('customers:api_customer_contacts', args=[self.customer2.pk])
        response2 = self.client.get(url2)
        data2 = response2.json()

        self.assertEqual(len(data1['contacts']), 2)
        self.assertEqual(len(data2['contacts']), 1)
        self.assertEqual(data2['contacts'][0]['name'], '王五')
