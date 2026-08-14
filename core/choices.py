from django.db import models


class RegionChoices(models.TextChoices):
    INDIA = "INDIA", "India"
    UAE = "UAE", "UAE"
    UK = "UK", "UK"
    USA = "USA", "USA"


class LanguageChoices(models.TextChoices):
    ENGLISH = "en", "English"
    ARABIC = "ar", "Arabic"


class CurrencyChoices(models.TextChoices):
    INR = "INR", "Indian Rupee"
    GBP = "GBP", "British Pound"
    USD = "USD", "US Dollar"


class StatusChoices(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"


class ProductTypeChoices(models.TextChoices):
    PHYSICAL = "physical", "Physical"
    DIGITAL = "digital", "Digital"


class ProductStatusChoices(models.TextChoices):
    DRAFT = "draft", "Draft"
    ACTIVE = "active", "Active"
    OUT_OF_STOCK = "out_of_stock", "Out of Stock"
    ARCHIVED = "archived", "Archived"


class PaymentStatusChoices(models.TextChoices):
    PENDING = "pending", "Pending"
    AUTHORIZED = "authorized", "Authorized"
    PAID = "paid", "Paid"
    FAILED = "failed", "Failed"
    REFUNDED = "refunded", "Refunded"


class OrderStatusChoices(models.TextChoices):
    PENDING = "pending", "Pending"
    CONFIRMED = "confirmed", "Confirmed"
    PROCESSING = "processing", "Processing"
    SHIPPED = "shipped", "Shipped"
    DELIVERED = "delivered", "Delivered"
    CANCELLED = "cancelled", "Cancelled"


class PaymentMethodChoices(models.TextChoices):
    RAZORPAY = "razorpay", "Razorpay"
    STRIPE = "stripe", "Stripe"
    COD = "cod", "Cash on Delivery"


class CouponTypeChoices(models.TextChoices):
    PERCENTAGE = "percentage", "Percentage"
    FIXED = "fixed", "Fixed"


class BannerPositionChoices(models.TextChoices):
    HERO = "hero", "Hero"
    HOME_MIDDLE = "home_middle", "Home Middle"
    CATEGORY_TOP = "category_top", "Category Top"


class DeviceChoices(models.TextChoices):
    MOBILE = "mobile", "Mobile"
    DESKTOP = "desktop", "Desktop"
    BOTH = "both", "Both"
