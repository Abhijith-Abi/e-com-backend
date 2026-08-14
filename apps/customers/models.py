from django.conf import settings
from django.db import models

from core.base_models import BaseModel
from core.choices import CurrencyChoices, LanguageChoices, RegionChoices


class CustomerProfile(BaseModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer_profile",
    )
    preferred_language = models.CharField(
        max_length=2,
        choices=LanguageChoices.choices,
        default=LanguageChoices.ENGLISH,
        db_index=True,
    )
    preferred_currency = models.CharField(
        max_length=3,
        choices=CurrencyChoices.choices,
        default=CurrencyChoices.INR,
        db_index=True,
    )
    is_suspended = models.BooleanField(default=False, db_index=True)
    country = models.CharField(
        max_length=10,
        choices=RegionChoices.choices,
        default=RegionChoices.INDIA,
        db_index=True,
    )

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("preferred_language", "preferred_currency")),
        ]

    def __str__(self):
        return self.user.email


class CustomerAddress(BaseModel):
    customer = models.ForeignKey(
        "customers.CustomerProfile",
        on_delete=models.CASCADE,
        related_name="addresses",
    )
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, default="")
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ("-is_default", "-created_at")

    def __str__(self):
        return f"{self.full_name} - {self.city}, {self.country}"


class Wishlist(BaseModel):
    customer = models.ForeignKey(
        "customers.CustomerProfile",
        on_delete=models.CASCADE,
        related_name="wishlists",
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="wishlisted_by",
    )

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(fields=("customer", "product"), name="unique_customer_wishlist_product"),
        ]

    def __str__(self):
        return f"{self.customer} -> {self.product}"
