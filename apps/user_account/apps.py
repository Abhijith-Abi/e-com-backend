from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    name = "apps.user_account"
    verbose_name = _("Users")

    # def ready(self):
    #     try:
    #         import apps.user_account.signals  # noqa: F401
    #     except ImportError:
    #         pass
