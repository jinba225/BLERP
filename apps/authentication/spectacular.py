"""
drf-spectacular extensions for custom authentication classes.
"""

from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework.authentication import BaseAuthentication
from .authentication import JWTAuthentication


class JWTAuthenticationExtension(OpenApiAuthenticationExtension):
    """
    drf-spectacular extension for JWTAuthentication.
    """

    name = 'JWTAuthentication'
    target_class = JWTAuthentication
    match_subclasses = True

    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
            'description': 'JWT Bearer token authentication. '
                          'Include the token in the Authorization header: '
                          'Bearer <your_jwt_token>',
        }


def register_authentication_extensions(endpoints=None):
    """
    Register all custom authentication extensions.
    This function should be called during Django app initialization.
    """
    OpenApiAuthenticationExtension.register(JWTAuthentication)
