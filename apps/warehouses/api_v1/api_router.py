from rest_framework.routers import SimpleRouter

from apps.warehouses.api_v1.views import WarehouseViewSet

app_name = "warehouses_api_v1"

router = SimpleRouter()
router.register("", WarehouseViewSet, basename="warehouses")

urlpatterns = router.urls

