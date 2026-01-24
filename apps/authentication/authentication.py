"""
JWT Authentication for the ERP system.
"""
import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import authentication, exceptions
from rest_framework.authentication import BaseAuthentication

User = get_user_model()


class JWTAuthentication(BaseAuthentication):
    """
    JWT token based authentication.
    """
    authentication_header_prefix = 'Bearer'

    def authenticate(self, request):
        """
        Authenticate the request and return a two-tuple of (user, token).
        """
        request.user = None

        # Get the authorization header
        auth_header = authentication.get_authorization_header(request).split()
        auth_header_prefix = self.authentication_header_prefix.lower()

        if not auth_header:
            return None

        if len(auth_header) == 1:
            # Invalid token header. No credentials provided.
            return None

        elif len(auth_header) > 2:
            # Invalid token header. Token string should not contain spaces.
            return None

        # Decode the header to get the prefix and token
        prefix = auth_header[0].decode('utf-8')
        token = auth_header[1].decode('utf-8')

        if prefix.lower() != auth_header_prefix:
            # The auth header prefix is not what we expected.
            return None

        return self._authenticate_credentials(request, token)

    def _authenticate_credentials(self, request, token):
        """
        Try to authenticate the given credentials.
        """
        try:
            payload = jwt.decode(
                token, 
                settings.JWT_SECRET_KEY, 
                algorithms=[settings.JWT_ALGORITHM]
            )
        except jwt.ExpiredSignatureError:
            msg = 'Token已过期'
            raise exceptions.AuthenticationFailed(msg)
        except jwt.InvalidTokenError:
            msg = '无效的Token'
            raise exceptions.AuthenticationFailed(msg)

        try:
            user = User.objects.get(pk=payload['user_id'])
        except User.DoesNotExist:
            msg = '用户不存在'
            raise exceptions.AuthenticationFailed(msg)

        if not user.is_active:
            msg = '用户已被禁用'
            raise exceptions.AuthenticationFailed(msg)

        return (user, token)


def generate_jwt_token(user):
    """
    Generate JWT token for the given user.
    """
    import datetime
    
    payload = {
        'user_id': user.pk,
        'username': user.username,
        'email': user.email,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=settings.JWT_EXPIRATION_DELTA),
        'iat': datetime.datetime.utcnow(),
    }

    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    return token