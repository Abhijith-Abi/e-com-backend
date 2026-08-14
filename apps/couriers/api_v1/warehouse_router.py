from rest_framework.routers import SimpleRouter
from apps.couriers.api_v1.views import WarehouseScopedCourierViewSet

router = SimpleRouter()
router.register("", WarehouseScopedCourierViewSet, basename="warehouse-couriers")

urlpatterns = router.urls
