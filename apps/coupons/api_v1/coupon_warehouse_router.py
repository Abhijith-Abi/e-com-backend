from django.urls import path

from apps.coupons.api_v1.views import ApplyCouponView

urlpatterns = [
    path("apply-coupon/", ApplyCouponView.as_view(), name="warehouse-apply-coupon"),
]
