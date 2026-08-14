from apps.settings.models import CurrencySettings, ShippingSettings, StoreSettings


class StoreSettingsRepository:
    @staticmethod
    def list_store_settings():
        return StoreSettings.objects.order_by("-created_at")

    @staticmethod
    def get_by_warehouse(warehouse_id):
        return StoreSettings.objects.filter(warehouse_id=warehouse_id).first()

    @staticmethod
    def get_global():
        return StoreSettings.objects.filter(warehouse__isnull=True).first()


class CurrencySettingsRepository:
    @staticmethod
    def list_currency_settings():
        return CurrencySettings.objects.order_by("-created_at")


class ShippingSettingsRepository:
    @staticmethod
    def list_shipping_settings():
        return ShippingSettings.objects.order_by("-created_at")
