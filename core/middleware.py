"""
Core middleware for the ERP system.
"""
import pytz
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin


class TimezoneMiddleware(MiddlewareMixin):
    """
    Middleware to set timezone based on user preferences.
    """
    def process_request(self, request):
        if request.user.is_authenticated:
            try:
                # Try to get timezone from user profile
                user_timezone = request.user.userprofile.timezone
                timezone.activate(pytz.timezone(user_timezone))
            except:
                # Fall back to default timezone
                timezone.deactivate()
        else:
            timezone.deactivate()