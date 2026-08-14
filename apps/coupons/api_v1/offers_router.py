from rest_framework.routers import SimpleRouter

from apps.coupons.api_v1.views import OfferViewSet

app_name = "offers_api_v1"

router = SimpleRouter()
router.register("", OfferViewSet, basename="offers")

urlpatterns = router.urls
