from django.conf import settings


def allauth_settings(request):
    """
    Expose allauth settings to templates.
    """
    return {
        "ACCOUNT_ALLOW_REGISTRATION": getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True),
    }
