from rest_framework.routers import SimpleRouter

from apps.orders.api_v1.views import WarehouseScopedOrderViewSet

app_name = "warehouse_orders_api_v1"

router = SimpleRouter()
router.register("records", WarehouseScopedOrderViewSet, basename="warehouse-orders")

urlpatterns = router.urls
