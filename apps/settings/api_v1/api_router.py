from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.settings.api_v1.views import (
    CurrencySettingsViewSet,
    ShippingSettingsViewSet,
    StoreSettingsSingletonView,
)

app_name = "settings_api_v1"

router = DefaultRouter()
router.register("currency", CurrencySettingsViewSet, basename="currency-settings")
router.register("shipping", ShippingSettingsViewSet, basename="shipping-settings")

urlpatterns = [
    path("store/", StoreSettingsSingletonView.as_view(), name="store-settings"),
] + router.urls
