from django.urls import path

from apps.settings.api_v1.views import WarehouseStoreSettingsSingletonView

app_name = "warehouse_settings_api_v1"

urlpatterns = [
    path("store/", WarehouseStoreSettingsSingletonView.as_view(), name="warehouse-store-settings"),
]
