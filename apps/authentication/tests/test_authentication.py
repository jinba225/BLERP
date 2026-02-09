"""
Authentication tests.
"""
from datetime import datetime, timedelta

import jwt
from authentication.authentication import JWTAuthentication, generate_jwt_token
from authentication.views import get_client_ip
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from rest_framework.exceptions import AuthenticationFailed

User = get_user_model()


class JWTTokenGenerationTest(TestCase):
    """Test JWT token generation."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="pass123"
        )

    def test_generate_jwt_token(self):
        """Test JWT token generation."""
        token = generate_jwt_token(self.user)

        # Token should be a string
        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 0)

    def test_token_payload(self):
        """Test JWT token payload contains correct information."""
        token = generate_jwt_token(self.user)

        # Decode token
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

        # Verify payload
        self.assertEqual(payload["user_id"], self.user.pk)
        self.assertEqual(payload["username"], self.user.username)
        self.assertEqual(payload["email"], self.user.email)
        self.assertIn("exp", payload)
        self.assertIn("iat", payload)

    def test_token_expiration(self):
        """Test JWT token expiration time."""
        token = generate_jwt_token(self.user)

        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

        # Check expiration is set correctly
        exp_time = datetime.utcfromtimestamp(payload["exp"])
        iat_time = datetime.utcfromtimestamp(payload["iat"])

        delta = exp_time - iat_time
        expected_delta = timedelta(seconds=settings.JWT_EXPIRATION_DELTA)

        # Allow 1 second tolerance
        self.assertAlmostEqual(delta.total_seconds(), expected_delta.total_seconds(), delta=1)


class JWTAuthenticationTest(TestCase):
    """Test JWT authentication class."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="pass123"
        )
        self.factory = RequestFactory()
        self.auth = JWTAuthentication()

    def test_authenticate_with_valid_token(self):
        """Test authentication with valid token."""
        token = generate_jwt_token(self.user)

        # Create request with token
        request = self.factory.get("/")
        request.META["HTTP_AUTHORIZATION"] = f"Bearer {token}"

        # Authenticate
        result = self.auth.authenticate(request)

        self.assertIsNotNone(result)
        user, auth_token = result
        self.assertEqual(user, self.user)
        self.assertEqual(auth_token, token)

    def test_authenticate_without_header(self):
        """Test authentication without authorization header."""
        request = self.factory.get("/")

        # Should return None (not raise exception)
        result = self.auth.authenticate(request)
        self.assertIsNone(result)

    def test_authenticate_with_invalid_prefix(self):
        """Test authentication with invalid prefix."""
        token = generate_jwt_token(self.user)

        request = self.factory.get("/")
        request.META["HTTP_AUTHORIZATION"] = f"Token {token}"

        # Should return None
        result = self.auth.authenticate(request)
        self.assertIsNone(result)

    def test_authenticate_with_expired_token(self):
        """Test authentication with expired token."""
        # Create an expired token
        payload = {
            "user_id": self.user.pk,
            "username": self.user.username,
            "email": self.user.email,
            "exp": datetime.utcnow() - timedelta(hours=1),  # Expired 1 hour ago
            "iat": datetime.utcnow() - timedelta(hours=2),
        }

        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

        request = self.factory.get("/")
        request.META["HTTP_AUTHORIZATION"] = f"Bearer {token}"

        # Should raise AuthenticationFailed
        with self.assertRaises(AuthenticationFailed) as context:
            self.auth.authenticate(request)

        self.assertIn("过期", str(context.exception))

    def test_authenticate_with_invalid_token(self):
        """Test authentication with invalid token."""
        request = self.factory.get("/")
        request.META["HTTP_AUTHORIZATION"] = "Bearer invalid_token_string"

        # Should raise AuthenticationFailed
        with self.assertRaises(AuthenticationFailed) as context:
            self.auth.authenticate(request)

        self.assertIn("无效", str(context.exception))

    def test_authenticate_with_nonexistent_user(self):
        """Test authentication with token for non-existent user."""
        # Create token for non-existent user
        payload = {
            "user_id": 99999,  # Non-existent user ID
            "username": "nonexistent",
            "email": "none@example.com",
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow(),
        }

        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

        request = self.factory.get("/")
        request.META["HTTP_AUTHORIZATION"] = f"Bearer {token}"

        # Should raise AuthenticationFailed
        with self.assertRaises(AuthenticationFailed) as context:
            self.auth.authenticate(request)

        self.assertIn("不存在", str(context.exception))

    def test_authenticate_with_inactive_user(self):
        """Test authentication with inactive user."""
        # Create inactive user
        inactive_user = User.objects.create_user(
            username="inactive", email="inactive@example.com", password="pass123", is_active=False
        )

        token = generate_jwt_token(inactive_user)

        request = self.factory.get("/")
        request.META["HTTP_AUTHORIZATION"] = f"Bearer {token}"

        # Should raise AuthenticationFailed
        with self.assertRaises(AuthenticationFailed) as context:
            self.auth.authenticate(request)

        self.assertIn("禁用", str(context.exception))

    def test_authenticate_with_single_part_header(self):
        """Test authentication with single-part header."""
        request = self.factory.get("/")
        request.META["HTTP_AUTHORIZATION"] = "Bearer"

        # Should return None (invalid header format)
        result = self.auth.authenticate(request)
        self.assertIsNone(result)

    def test_authenticate_with_multi_part_header(self):
        """Test authentication with header containing spaces."""
        token = generate_jwt_token(self.user)

        request = self.factory.get("/")
        request.META["HTTP_AUTHORIZATION"] = f"Bearer {token} extra_part"

        # Should return None (invalid header format)
        result = self.auth.authenticate(request)
        self.assertIsNone(result)


class GetClientIPTest(TestCase):
    """Test get_client_ip utility function."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()

    def test_get_ip_from_remote_addr(self):
        """Test getting IP from REMOTE_ADDR."""
        request = self.factory.get("/")
        request.META["REMOTE_ADDR"] = "192.168.1.100"

        ip = get_client_ip(request)
        self.assertEqual(ip, "192.168.1.100")

    def test_get_ip_from_x_forwarded_for(self):
        """Test getting IP from X-Forwarded-For header."""
        request = self.factory.get("/")
        request.META["HTTP_X_FORWARDED_FOR"] = "203.0.113.1, 203.0.113.2"
        request.META["REMOTE_ADDR"] = "192.168.1.100"

        # Should return the first IP from X-Forwarded-For
        ip = get_client_ip(request)
        self.assertEqual(ip, "203.0.113.1")

    def test_get_ip_from_single_x_forwarded_for(self):
        """Test getting IP from X-Forwarded-For with single IP."""
        request = self.factory.get("/")
        request.META["HTTP_X_FORWARDED_FOR"] = "203.0.113.1"
        request.META["REMOTE_ADDR"] = "192.168.1.100"

        ip = get_client_ip(request)
        self.assertEqual(ip, "203.0.113.1")
