from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class AccountAdapter(DefaultAccountAdapter):
    """Custom account adapter for django-allauth"""
    pass


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """Custom social account adapter for django-allauth"""
    pass
