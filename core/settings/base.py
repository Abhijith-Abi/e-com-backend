import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve(strict=True).parent.parent.parent
APPS_DIR = BASE_DIR / "apps"
if (BASE_DIR / ".env").exists():
    with open(BASE_DIR / ".env", "r", encoding="utf-8") as env_file:
        for line in env_file:
            if "=" not in line or line.lstrip().startswith("#"):
                continue
            key, value = line.strip().split("=", 1)
            os.environ.setdefault(key, value)


def env(key, default=None):
    return os.getenv(key, default)


def env_bool(key, default=False):
    return env(key, str(default)).lower() in {"1", "true", "yes", "on"}


def env_int(key, default=0):
    return int(env(key, default))


def env_list(key, default=None):
    value = env(key)
    if not value:
        return default or []
    return [item.strip() for item in value.split(",") if item.strip()]



DEBUG = env_bool("DJANGO_DEBUG", default=False)
SECRET_KEY = env("DJANGO_SECRET_KEY", default="unsafe-default-secret-key")
ADMIN_REGISTRATION_SECRET = env("ADMIN_REGISTRATION_SECRET", default="house-of-vaz-admin-secret")
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", default=["*"])

TIME_ZONE = env("TIME_ZONE", default="Asia/Kolkata")
LANGUAGE_CODE = "en"
LANGUAGES = (
    ("en", "English"),
    ("ar", "Arabic"),
)
USE_I18N = True
USE_TZ = True
SITE_ID = 1

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
ROOT_URLCONF = "core.urls"
WSGI_APPLICATION = "core.wsgi.application"

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "anymail",
]

THIRD_PARTY_APPS = [
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "django_filters",
]

LOCAL_APPS = [
    "apps.user_account",
    "apps.warehouses",
    "apps.categories",
    "apps.products",
    "apps.cart",
    "apps.orders",
    "apps.payments",
    "apps.coupons",
    "apps.customers",
    "apps.banners",
    "apps.analytics",
    "apps.settings",
    "apps.gift_cards",
    "apps.couriers",
    "apps.redeem",
    "apps.notifications",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS
AUTH_USER_MODEL = "user_account.User"

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.WarehouseScopingMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [str(BASE_DIR / "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
        "ATOMIC_REQUESTS": True,
        "OPTIONS": {
            "timeout": 20,
        },
    }
}

ANYMAIL = {
    "RESEND_API_KEY": env("RESEND_API_KEY"),
}
RESEND_API_KEY = env("RESEND_API_KEY")

EMAIL_BACKEND = "anymail.backends.resend.EmailBackend"
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@info.abisolutions.online")

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = "DENY"

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "core.authentication.OptionalJWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "core.pagination.CustomPageNumberPagination",
    "PAGE_SIZE": 20,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "House Of Vaz API",
    "DESCRIPTION": (
        "Multi-region, multi-currency e-commerce backend API.\n\n"
        "## Authentication\n"
        "Use `POST /api/v1/auth/login/` to obtain a JWT token, then pass it as:\n"
        "`Authorization: Bearer <access_token>`\n\n"
        "## Pagination\n"
        "All list endpoints support `?page=1&page_size=20`.\n\n"
        "## Filtering & Search\n"
        "Filter fields are listed per endpoint. Use `?search=` for text search and `?ordering=` for sorting."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SORT_OPERATIONS": False,
    "ENUM_GENERATE_CHOICE_DESCRIPTION": True,
    "SCHEMA_PATH_PREFIX": r"/api/v1/",
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "persistAuthorization": True,
        "displayOperationId": False,
        "defaultModelsExpandDepth": 2,
        "defaultModelExpandDepth": 2,
        "docExpansion": "list",
        "filter": True,
        "showExtensions": True,
        "showCommonExtensions": True,
        "tryItOutEnabled": True,
    },
    "TAGS": [
        {"name": "Auth", "description": "User registration, login, profile, password reset"},
        {"name": "Warehouses", "description": "Warehouse CRUD and management"},
        {"name": "Warehouse Products", "description": "Products scoped to a specific warehouse"},
        {"name": "Warehouse Categories", "description": "Categories scoped to a specific warehouse"},
        {"name": "Warehouse Banners", "description": "Banners scoped to a specific warehouse"},
        {"name": "Categories", "description": "Product category CRUD"},
        {"name": "Products", "description": "Product, product images, and warehouse stock management"},
        {"name": "Customers", "description": "Customer profiles and wishlists"},
        {"name": "Cart", "description": "Shopping cart and cart items"},
        {"name": "Orders", "description": "Order management"},
        {"name": "Payments", "description": "Payment records"},
        {"name": "Coupons", "description": "Coupon/discount code management"},
        {"name": "Offers", "description": "Promotional offer management"},
        {"name": "Warehouse Offers", "description": "Offers scoped to a specific warehouse"},
        {"name": "Banners", "description": "Promotional banner management"},
        {"name": "Analytics", "description": "Store analytics"},
        {"name": "Warehouse Analytics", "description": "Analytics scoped to a specific warehouse"},
        {"name": "Warehouse Orders", "description": "Orders scoped to a specific warehouse"},
        {"name": "Settings", "description": "Store, currency, and shipping settings"},
        {"name": "Warehouse Settings", "description": "Store settings scoped to a specific warehouse"},
        {"name": "Warehouse Gift Card Categories", "description": "Gift card categories scoped to a specific warehouse"},
        {"name": "Warehouse Gift Card Wraps", "description": "Gift card wraps scoped to a specific warehouse"},
        {"name": "Warehouse Gift Cards", "description": "Gift cards scoped to a specific warehouse"},
        {"name": "Redeem – Wallet", "description": "Customer point wallet and transaction history"},
        {"name": "Redeem – Bills", "description": "Customer bill uploads for point earning"},
        {"name": "Redeem – Admin", "description": "Admin tools: review bills, award points, view wallets and transactions"},
        {"name": "Redeem – Settings", "description": "Global points/redeem configuration (admin)"},
        {"name": "Redeem – Checkout", "description": "Preview and apply point redemption at checkout"},
        {"name": "Redeem – Product", "description": "Redeem a product entirely using loyalty points"},
    ],
    "ENUM_NAME_OVERRIDES": {
        "StatusEnum": "core.choices.StatusChoices",
        "CurrencyEnum": "core.choices.CurrencyChoices",
        "RegionEnum": "core.choices.RegionChoices",
        "LanguageEnum": "core.choices.LanguageChoices",
        "ProductStatusEnum": "core.choices.ProductStatusChoices",
        "ProductTypeEnum": "core.choices.ProductTypeChoices",
        "OrderStatusEnum": "core.choices.OrderStatusChoices",
        "PaymentStatusEnum": "core.choices.PaymentStatusChoices",
        "PaymentMethodEnum": "core.choices.PaymentMethodChoices",
        "CouponTypeEnum": "core.choices.CouponTypeChoices",
        "BannerPositionEnum": "core.choices.BannerPositionChoices",
        "DeviceEnum": "core.choices.DeviceChoices",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=7),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_HEADERS = [
    "accept",
    "authorization",
    "content-type",
    "x-admin-secret",
]
