"""
Core models tests.
"""
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.core.models import (
    Attachment,
    AuditLog,
    Company,
    DocumentNumberSequence,
    Notification,
    SystemConfig,
)

User = get_user_model()


class CompanyModelTest(TestCase):
    """Test Company model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="pass123"
        )

    def test_company_creation(self):
        """Test company creation."""
        company = Company.objects.create(
            name="测试公司",
            code="TEST001",
            legal_representative="张三",
            registration_number="91110000XXXXXXXX",
            tax_number="91110000XXXXXXXX",
            address="北京市朝阳区",
            phone="010-12345678",
            fax="010-87654321",
            email="info@test.com",
            website="https://test.com",
            description="测试公司描述",
            created_by=self.user,
        )

        self.assertEqual(company.name, "测试公司")
        self.assertEqual(company.code, "TEST001")
        self.assertTrue(company.is_active)
        self.assertFalse(company.is_deleted)

    def test_company_unique_code(self):
        """Test company code uniqueness."""
        Company.objects.create(name="公司A", code="COMP001", created_by=self.user)

        # Try to create another company with same code
        with self.assertRaises(Exception):
            Company.objects.create(name="公司B", code="COMP001", created_by=self.user)

    def test_company_soft_delete(self):
        """Test company soft delete."""
        company = Company.objects.create(name="测试公司", code="TEST001", created_by=self.user)

        # Soft delete
        company.delete()

        # Should still exist in database but marked as deleted
        company.refresh_from_db()
        self.assertTrue(company.is_deleted)
        self.assertIsNotNone(company.deleted_at)

    def test_company_hard_delete(self):
        """Test company hard delete."""
        company = Company.objects.create(name="测试公司", code="TEST001", created_by=self.user)

        company_id = company.id

        # Hard delete
        company.hard_delete()

        # Should not exist in database
        self.assertFalse(Company.objects.filter(id=company_id).exists())

    def test_company_str_representation(self):
        """Test company string representation."""
        company = Company.objects.create(name="测试公司", code="TEST001", created_by=self.user)

        self.assertEqual(str(company), "测试公司")


class SystemConfigModelTest(TestCase):
    """Test SystemConfig model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="pass123"
        )

    def test_config_creation(self):
        """Test system config creation."""
        config = SystemConfig.objects.create(
            key="max_login_attempts",
            value="5",
            config_type="security",
            description="最大登录尝试次数",
            created_by=self.user,
        )

        self.assertEqual(config.key, "max_login_attempts")
        self.assertEqual(config.value, "5")
        self.assertEqual(config.config_type, "security")
        self.assertTrue(config.is_active)

    def test_config_unique_key(self):
        """Test config key uniqueness."""
        SystemConfig.objects.create(key="test_key", value="value1", created_by=self.user)

        # Try to create another config with same key
        with self.assertRaises(Exception):
            SystemConfig.objects.create(key="test_key", value="value2", created_by=self.user)

    def test_config_types(self):
        """Test all config types."""
        types = ["system", "business", "ui", "security"]

        for config_type in types:
            config = SystemConfig.objects.create(
                key=f"test_{config_type}",
                value="test_value",
                config_type=config_type,
                created_by=self.user,
            )
            self.assertEqual(config.config_type, config_type)

    def test_config_str_representation(self):
        """Test config string representation."""
        config = SystemConfig.objects.create(
            key="test_key", value="test_value", created_by=self.user
        )

        expected = "test_key: test_value"
        self.assertEqual(str(config), expected)


class AttachmentModelTest(TestCase):
    """Test Attachment model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="pass123"
        )

    def test_attachment_creation(self):
        """Test attachment creation."""
        file_content = b"test file content"
        test_file = SimpleUploadedFile("test.txt", file_content)

        attachment = Attachment.objects.create(
            name="测试文件",
            file=test_file,
            file_type="document",
            file_size=len(file_content),
            mime_type="text/plain",
            description="测试附件",
            created_by=self.user,
        )

        self.assertEqual(attachment.name, "测试文件")
        self.assertEqual(attachment.file_type, "document")
        self.assertEqual(attachment.file_size, len(file_content))

    def test_attachment_types(self):
        """Test all attachment types."""
        types = ["image", "document", "video", "audio", "other"]

        for file_type in types:
            test_file = SimpleUploadedFile(f"test_{file_type}.txt", b"content")
            attachment = Attachment.objects.create(
                name=f"测试{file_type}", file=test_file, file_type=file_type, created_by=self.user
            )
            self.assertEqual(attachment.file_type, file_type)

    def test_file_size_display_bytes(self):
        """Test file size display for bytes."""
        test_file = SimpleUploadedFile("test.txt", b"x" * 500)
        attachment = Attachment.objects.create(
            name="测试文件", file=test_file, file_size=500, created_by=self.user
        )

        self.assertEqual(attachment.file_size_display, "500 B")

    def test_file_size_display_kb(self):
        """Test file size display for KB."""
        test_file = SimpleUploadedFile("test.txt", b"content")
        attachment = Attachment.objects.create(
            name="测试文件", file=test_file, file_size=2048, created_by=self.user  # 2 KB
        )

        self.assertEqual(attachment.file_size_display, "2.0 KB")

    def test_file_size_display_mb(self):
        """Test file size display for MB."""
        test_file = SimpleUploadedFile("test.txt", b"content")
        attachment = Attachment.objects.create(
            name="测试文件", file=test_file, file_size=2 * 1024 * 1024, created_by=self.user  # 2 MB
        )

        self.assertEqual(attachment.file_size_display, "2.0 MB")

    def test_file_size_display_gb(self):
        """Test file size display for GB."""
        test_file = SimpleUploadedFile("test.txt", b"content")
        attachment = Attachment.objects.create(
            name="测试文件",
            file=test_file,
            file_size=3 * 1024 * 1024 * 1024,  # 3 GB
            created_by=self.user,
        )

        self.assertEqual(attachment.file_size_display, "3.0 GB")

    def test_attachment_str_representation(self):
        """Test attachment string representation."""
        test_file = SimpleUploadedFile("test.txt", b"content")
        attachment = Attachment.objects.create(name="测试文件", file=test_file, created_by=self.user)

        self.assertEqual(str(attachment), "测试文件")


class AuditLogModelTest(TestCase):
    """Test AuditLog model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="pass123"
        )

    def test_audit_log_creation(self):
        """Test audit log creation."""
        log = AuditLog.objects.create(
            user=self.user,
            action="create",
            model_name="Product",
            object_id="123",
            object_repr="测试产品",
            changes={"name": ["", "测试产品"]},
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
        )

        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action, "create")
        self.assertEqual(log.model_name, "Product")
        self.assertEqual(log.object_id, "123")

    def test_audit_log_action_types(self):
        """Test all action types."""
        actions = ["create", "update", "delete", "view", "login", "logout", "export", "import"]

        for action in actions:
            log = AuditLog.objects.create(
                user=self.user, action=action, model_name="TestModel", ip_address="192.168.1.1"
            )
            self.assertEqual(log.action, action)

    def test_audit_log_changes_json(self):
        """Test audit log changes as JSON."""
        changes = {"name": ["旧名称", "新名称"], "price": [100, 150], "is_active": [True, False]}

        log = AuditLog.objects.create(
            user=self.user,
            action="update",
            model_name="Product",
            changes=changes,
            ip_address="192.168.1.1",
        )

        self.assertEqual(log.changes, changes)

    def test_audit_log_ordering(self):
        """Test audit logs are ordered by timestamp desc."""
        log1 = AuditLog.objects.create(
            user=self.user, action="create", model_name="Product", ip_address="192.168.1.1"
        )

        log2 = AuditLog.objects.create(
            user=self.user, action="update", model_name="Product", ip_address="192.168.1.1"
        )

        logs = list(AuditLog.objects.all())
        self.assertEqual(logs[0], log2)  # Latest first
        self.assertEqual(logs[1], log1)

    def test_audit_log_str_representation(self):
        """Test audit log string representation."""
        log = AuditLog.objects.create(
            user=self.user, action="create", model_name="Product", ip_address="192.168.1.1"
        )

        # User str includes email, so expected format is: "username (email) - action - timestamp"
        expected = f"{self.user} - create - {log.timestamp}"
        self.assertEqual(str(log), expected)


class DocumentNumberSequenceModelTest(TestCase):
    """Test DocumentNumberSequence model."""

    def test_sequence_creation(self):
        """Test sequence creation."""
        sequence = DocumentNumberSequence.objects.create(
            prefix="SO", date_str="20251112", current_number=1
        )

        self.assertEqual(sequence.prefix, "SO")
        self.assertEqual(sequence.date_str, "20251112")
        self.assertEqual(sequence.current_number, 1)

    def test_sequence_unique_together(self):
        """Test unique_together constraint."""
        DocumentNumberSequence.objects.create(prefix="SO", date_str="20251112", current_number=1)

        # Try to create duplicate
        with self.assertRaises(Exception):
            DocumentNumberSequence.objects.create(
                prefix="SO", date_str="20251112", current_number=2
            )

    def test_different_dates_same_prefix(self):
        """Test same prefix can have different dates."""
        seq1 = DocumentNumberSequence.objects.create(
            prefix="SO", date_str="20251112", current_number=5
        )

        seq2 = DocumentNumberSequence.objects.create(
            prefix="SO", date_str="20251113", current_number=1
        )

        self.assertEqual(seq1.prefix, seq2.prefix)
        self.assertNotEqual(seq1.date_str, seq2.date_str)

    def test_different_prefixes_same_date(self):
        """Test same date can have different prefixes."""
        seq1 = DocumentNumberSequence.objects.create(
            prefix="SO", date_str="20251112", current_number=5
        )

        seq2 = DocumentNumberSequence.objects.create(
            prefix="PO", date_str="20251112", current_number=3
        )

        self.assertEqual(seq1.date_str, seq2.date_str)
        self.assertNotEqual(seq1.prefix, seq2.prefix)

    def test_sequence_str_representation(self):
        """Test sequence string representation."""
        sequence = DocumentNumberSequence.objects.create(
            prefix="SO", date_str="20251112", current_number=5
        )

        expected = "SO20251112: 5"
        self.assertEqual(str(sequence), expected)


class NotificationModelTest(TestCase):
    """Test Notification model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="pass123"
        )

    def test_notification_creation(self):
        """Test notification creation."""
        notification = Notification.objects.create(
            recipient=self.user,
            title="测试通知",
            message="这是一条测试通知消息",
            notification_type="info",
            category="system",
        )

        self.assertEqual(notification.recipient, self.user)
        self.assertEqual(notification.title, "测试通知")
        self.assertFalse(notification.is_read)

    def test_notification_types(self):
        """Test all notification types."""
        types = ["info", "success", "warning", "error"]

        for notif_type in types:
            notification = Notification.objects.create(
                recipient=self.user,
                title=f"{notif_type}通知",
                message="消息内容",
                notification_type=notif_type,
            )
            self.assertEqual(notification.notification_type, notif_type)

    def test_notification_categories(self):
        """Test all notification categories."""
        categories = [
            "sales_return",
            "sales_order",
            "purchase_order",
            "inventory",
            "finance",
            "system",
        ]

        for category in categories:
            notification = Notification.objects.create(
                recipient=self.user, title=f"{category}通知", message="消息内容", category=category
            )
            self.assertEqual(notification.category, category)

    def test_mark_as_read(self):
        """Test mark notification as read."""
        notification = Notification.objects.create(
            recipient=self.user, title="测试通知", message="消息内容"
        )

        self.assertFalse(notification.is_read)
        self.assertIsNone(notification.read_at)

        # Mark as read
        notification.mark_as_read()

        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)

    def test_mark_as_read_idempotent(self):
        """Test marking as read multiple times."""
        notification = Notification.objects.create(
            recipient=self.user, title="测试通知", message="消息内容"
        )

        notification.mark_as_read()
        first_read_at = notification.read_at

        # Mark as read again
        notification.mark_as_read()

        # read_at should not change
        self.assertEqual(notification.read_at, first_read_at)

    def test_create_notification_classmethod(self):
        """Test create_notification class method."""
        notification = Notification.create_notification(
            recipient=self.user,
            title="类方法创建的通知",
            message="这是通过类方法创建的通知",
            notification_type="success",
            category="sales_order",
            reference_type="SalesOrder",
            reference_id="12345",
            reference_url="/sales/orders/12345/",
        )

        self.assertIsInstance(notification, Notification)
        self.assertEqual(notification.recipient, self.user)
        self.assertEqual(notification.title, "类方法创建的通知")
        self.assertEqual(notification.notification_type, "success")
        self.assertEqual(notification.category, "sales_order")
        self.assertEqual(notification.reference_type, "SalesOrder")
        self.assertEqual(notification.reference_id, "12345")
        self.assertEqual(notification.reference_url, "/sales/orders/12345/")

    def test_notification_ordering(self):
        """Test notifications are ordered by created_at desc."""
        notif1 = Notification.objects.create(recipient=self.user, title="通知1", message="消息1")

        notif2 = Notification.objects.create(recipient=self.user, title="通知2", message="消息2")

        notifications = list(Notification.objects.filter(recipient=self.user))
        self.assertEqual(notifications[0], notif2)  # Latest first
        self.assertEqual(notifications[1], notif1)

    def test_notification_str_representation(self):
        """Test notification string representation."""
        notification = Notification.objects.create(
            recipient=self.user, title="测试通知", message="消息内容"
        )

        expected = "testuser - 测试通知"
        self.assertEqual(str(notification), expected)
