from .base import *  # noqa
from .base import env_bool

DEBUG = False
# No SSL redirect — nginx handles HTTP, no HTTPS in front
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_CONTENT_TYPE_NOSNIFF = True
