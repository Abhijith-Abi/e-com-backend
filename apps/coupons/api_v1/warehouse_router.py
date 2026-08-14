from rest_framework.routers import SimpleRouter

from apps.coupons.api_v1.views import WarehouseScopedOfferViewSet

app_name = "warehouse_offers_api_v1"

router = SimpleRouter()
router.register("", WarehouseScopedOfferViewSet, basename="warehouse-offers")

urlpatterns = router.urls
