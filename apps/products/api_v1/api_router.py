from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.products.api_v1.views import (
    NewProductsListView,
    ProductImageViewSet,
    ProductStatusChoicesView,
    ProductTypeChoicesView,
    ProductViewSet,
)
from apps.products.api_v1.views import LowStockNotificationViewSet


app_name = "products_api_v1"

router = DefaultRouter()
router.register("items", ProductViewSet, basename="products")
router.register("images", ProductImageViewSet, basename="product-images")
router.register("notifications", LowStockNotificationViewSet, basename="low-stock-notifications")

urlpatterns = router.urls + [
    path("new/", NewProductsListView.as_view(), name="new-products"),
    path("types/", ProductTypeChoicesView.as_view(), name="product-types"),
    path("statuses/", ProductStatusChoicesView.as_view(), name="product-statuses"),
]
