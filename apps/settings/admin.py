from django.contrib import admin

from apps.settings.models import CurrencySettings, ShippingSettings, StoreSettings


@admin.register(StoreSettings)
class StoreSettingsAdmin(admin.ModelAdmin):
    list_display = ("store_name_en", "store_email", "store_phone", "low_stock_threshold")


@admin.register(CurrencySettings)
class CurrencySettingsAdmin(admin.ModelAdmin):
    list_display = ("exchange_rate_inr", "exchange_rate_gbp", "exchange_rate_usd")


@admin.register(ShippingSettings)
class ShippingSettingsAdmin(admin.ModelAdmin):
    list_display = ("domestic", "international", "uk_domestic", "express_shipping")
