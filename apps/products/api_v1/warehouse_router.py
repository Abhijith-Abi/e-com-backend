from django.urls import path
from rest_framework.routers import SimpleRouter

from apps.products.api_v1.views import WarehouseBestSellersListView, WarehouseNewProductsListView, WarehouseScopedProductViewSet

app_name = "warehouse_products_api_v1"

router = SimpleRouter()
router.register("", WarehouseScopedProductViewSet, basename="warehouse-products")

urlpatterns = [
    path("new/", WarehouseNewProductsListView.as_view(), name="warehouse-new-products"),
    path("best-sellers/", WarehouseBestSellersListView.as_view(), name="warehouse-best-sellers"),
] + router.urls

