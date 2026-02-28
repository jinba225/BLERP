"""
Authentication views for the ERP system.
"""

from django.conf import settings
from django.contrib.auth import get_user_model, login, logout
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .authentication import generate_jwt_token
from .serializers import (
    LoginSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetSerializer,
    TokenSerializer,
    UserInfoSerializer,
)

User = get_user_model()


@extend_schema(
    request=LoginSerializer,
    responses={
        200: OpenApiResponse(
            description="登录成功",
            response=TokenSerializer,
        ),
        400: OpenApiResponse(
            description="登录失败",
        ),
    },
    summary="用户登录",
)
@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    """User login API."""
    serializer = LoginSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.validated_data["user"]

        # Generate JWT token
        token = generate_jwt_token(user)

        # Login user (for session-based auth as well)
        login(request, user)

        # Log login activity
        from users.models import LoginLog

        LoginLog.objects.create(
            user=user,
            login_type="web",
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            is_successful=True,
        )

        # Prepare response data
        user_serializer = UserInfoSerializer(user, context={"request": request})

        response_data = {
            "token": token,
            "user": user_serializer.data,
            "expires_in": settings.JWT_EXPIRATION_DELTA,
            "message": "登录成功",
        }

        return Response(response_data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="用户登出",
    responses={
        200: OpenApiResponse(
            description="登出成功",
        ),
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """User logout API."""
    # Update login log
    from django.utils import timezone
    from users.models import LoginLog

    try:
        login_log = LoginLog.objects.filter(user=request.user, logout_time__isnull=True).latest(
            "login_time"
        )
        login_log.logout_time = timezone.now()
        login_log.save()
    except LoginLog.DoesNotExist:
        pass

    # Logout user
    logout(request)

    return Response({"message": "登出成功"}, status=status.HTTP_200_OK)


@extend_schema(
    summary="获取当前用户信息",
    responses={
        200: OpenApiResponse(
            description="用户信息",
            response=UserInfoSerializer,
        ),
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_info_view(request):
    """Get current user info."""
    serializer = UserInfoSerializer(request.user, context={"request": request})
    return Response(serializer.data)


@extend_schema(
    request=PasswordChangeSerializer,
    summary="修改密码",
    responses={
        200: OpenApiResponse(
            description="密码修改成功",
        ),
        400: OpenApiResponse(
            description="密码修改失败",
        ),
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    """Change user password."""
    serializer = PasswordChangeSerializer(data=request.data, context={"request": request})

    if serializer.is_valid():
        serializer.save()
        return Response({"message": "密码修改成功"})

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=PasswordResetSerializer,
    summary="请求密码重置",
    responses={
        200: OpenApiResponse(
            description="密码重置邮件已发送",
        ),
        400: OpenApiResponse(
            description="请求失败",
        ),
        500: OpenApiResponse(
            description="发送邮件失败",
        ),
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
def password_reset_view(request):
    """Request password reset."""
    serializer = PasswordResetSerializer(data=request.data)

    if serializer.is_valid():
        email = serializer.validated_data["email"]
        try:
            user = User.objects.get(email=email, is_active=True)

            # Generate token and uid
            from django.contrib.auth.tokens import default_token_generator
            from django.core.mail import send_mail
            from django.utils.encoding import force_bytes
            from django.utils.http import urlsafe_base64_encode

            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            # Construct reset URL (assuming frontend handles this route)
            # In a real app, this should be a frontend URL
            reset_url = f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}"

            # Send email
            subject = "重置您的密码"
            message = f"""
            您好 {user.username}，

            您收到这封邮件是因为您请求重置密码。
            请点击下面的链接重置密码：

            {reset_url}

            如果您没有请求重置密码，请忽略此邮件。
            """

            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )

            return Response(
                {"message": "密码重置邮件已发送，请检查您的邮箱"},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            # For security reasons, don't reveal if email exists or not,
            # but here we already validated it in serializer so it's fine to log error
            print(f"Error sending email: {e}")
            return Response(
                {"message": "发送邮件失败，请稍后重试"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=PasswordResetConfirmSerializer,
    summary="确认密码重置",
    responses={
        200: OpenApiResponse(
            description="密码重置成功",
        ),
        400: OpenApiResponse(
            description="重置链接无效",
        ),
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
def password_reset_confirm_view(request):
    """Confirm password reset."""
    serializer = PasswordResetConfirmSerializer(data=request.data)

    if serializer.is_valid():
        uid = serializer.validated_data["uid"]
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_str
        from django.utils.http import urlsafe_base64_decode

        try:
            uid_str = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=uid_str)

            if default_token_generator.check_token(user, token):
                user.set_password(new_password)
                user.save()
                return Response(
                    {"message": "密码重置成功，请使用新密码登录"},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"error": "无效或过期的重置链接"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"error": "无效的重置链接"}, status=status.HTTP_400_BAD_REQUEST)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="刷新Token",
    responses={
        200: OpenApiResponse(
            description="Token刷新成功",
            response=TokenSerializer,
        ),
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def refresh_token_view(request):
    """Refresh JWT token."""
    token = generate_jwt_token(request.user)

    response_data = {
        "token": token,
        "expires_in": settings.JWT_EXPIRATION_DELTA,
        "message": "Token刷新成功",
    }

    return Response(response_data, status=status.HTTP_200_OK)


def get_client_ip(request):
    """Get client IP address."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        # Take first IP in list (client IP)
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip
