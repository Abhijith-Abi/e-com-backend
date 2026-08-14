from django.db import models

from core.base_models import BaseModel


class StoreSettings(BaseModel):
    warehouse = models.OneToOneField(
        "warehouses.Warehouse",
        on_delete=models.CASCADE,
        related_name="store_settings",
        null=True,
        blank=True,
    )
    store_name_en = models.CharField(max_length=255)
    store_name_ar = models.CharField(max_length=255, null=True, blank=True)
    store_email = models.EmailField()
    store_phone = models.CharField(max_length=50)
    low_stock_threshold = models.PositiveIntegerField(default=5)

    class Meta:
        verbose_name_plural = "Store settings"

    def __str__(self):
        return self.store_name_en


class CurrencySettings(BaseModel):
    exchange_rate_inr = models.DecimalField(max_digits=12, decimal_places=4, default=1)
    exchange_rate_gbp = models.DecimalField(max_digits=12, decimal_places=4, default=1)
    exchange_rate_usd = models.DecimalField(max_digits=12, decimal_places=4, default=1)

    class Meta:
        verbose_name_plural = "Currency settings"

    def __str__(self):
        return "Currency Settings"


class ShippingSettings(BaseModel):
    domestic = models.BooleanField(default=True)
    international = models.BooleanField(default=True)
    uk_domestic = models.BooleanField(default=True)
    shipping_price_inr = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_price_gbp = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_price_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    express_shipping = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Shipping settings"

    def __str__(self):
        return "Shipping Settings"
