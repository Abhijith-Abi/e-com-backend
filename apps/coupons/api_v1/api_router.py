from django.urls import path
from rest_framework.routers import SimpleRouter

from apps.coupons.api_v1.views import ApplyCouponView, CouponViewSet

app_name = "coupons_api_v1"

router = SimpleRouter()
router.register("", CouponViewSet, basename="coupons")

urlpatterns = router.urls + [
    path("apply-coupon/", ApplyCouponView.as_view(), name="apply-coupon"),
]
