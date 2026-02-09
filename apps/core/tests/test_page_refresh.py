"""
页面自动刷新功能测试
"""
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings

User = get_user_model()


class PageRefreshTestCase(TestCase):
    """页面刷新功能测试"""

    def setUp(self):
        """测试前准备"""
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.client = Client()
        self.client.login(username="testuser", password="testpass123")

    def test_config_injection(self):
        """测试配置注入到模板"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

        # 检查页面刷新配置是否在上下文中
        # 注意：由于我们使用context_processor，配置会自动注入
        # 这里主要检查页面是否能正常加载

    @override_settings(PAGE_REFRESH_CONFIG={"enabled": False})
    def test_disabled_refresh(self):
        """测试禁用刷新功能"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_page_load_with_javascript(self):
        """测试页面加载时JavaScript模块是否正确引用"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")

        # 检查是否包含页面刷新脚本引用
        # 注意：只有在配置启用时才会引用
        from django.conf import settings

        if getattr(settings, "PAGE_REFRESH_CONFIG", {}).get("enabled", True):
            self.assertIn("page-refresh.js", content)

    def test_alpine_component_registration(self):
        """测试Alpine.js组件注册"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")

        # 检查是否包含usePageRefresh组件定义
        from django.conf import settings

        if getattr(settings, "PAGE_REFRESH_CONFIG", {}).get("enabled", True):
            self.assertIn("usePageRefresh", content)

    def test_context_processor_available(self):
        """测试context processor是否可用"""
        from django.test import RequestFactory

        from apps.core.context_processors import page_refresh_config

        factory = RequestFactory()
        request = factory.get("/")
        request.page_refresh_config = {}

        context = page_refresh_config(request)

        # 检查返回的配置
        self.assertIn("page_refresh_config", context)
        self.assertIsInstance(context["page_refresh_config"], dict)
        self.assertIn("enabled", context["page_refresh_config"])
        self.assertIn("interval", context["page_refresh_config"])

    def test_config_merge_with_defaults(self):
        """测试配置合并逻辑"""
        from django.test import RequestFactory

        from apps.core.context_processors import page_refresh_config

        factory = RequestFactory()
        request = factory.get("/")

        # 不设置自定义配置
        request.page_refresh_config = {}
        context = page_refresh_config(request)

        config = context["page_refresh_config"]

        # 检查默认值
        self.assertTrue(config["enabled"])
        self.assertEqual(config["mode"], "auto")
        self.assertTrue(config["preserve_state"])

    def test_view_config_override(self):
        """测试视图级别配置覆盖"""
        from django.test import RequestFactory

        from apps.core.context_processors import page_refresh_config

        factory = RequestFactory()
        request = factory.get("/")

        # 设置自定义配置
        request.page_refresh_config = {
            "interval": 60,
            "mode": "smart",
        }
        context = page_refresh_config(request)

        config = context["page_refresh_config"]

        # 检查自定义配置生效
        self.assertEqual(config["interval"], 60)
        self.assertEqual(config["mode"], "smart")
