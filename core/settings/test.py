from .base import *  # noqa

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
SILENCED_SYSTEM_CHECKS = ["fields.E180"]

from django.db.backends.signals import connection_created

def _sqlite_json_valid_fallback(sender, connection, **kwargs):
    if connection.vendor == 'sqlite':
        cursor = connection.cursor()
        try:
            cursor.execute('SELECT JSON_VALID("{}")')
        except Exception:
            connection.connection.create_function("JSON_VALID", 1, lambda x: 1)

connection_created.connect(_sqlite_json_valid_fallback)
