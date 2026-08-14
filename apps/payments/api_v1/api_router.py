from rest_framework.routers import SimpleRouter

from apps.payments.api_v1.views import PaymentMethodViewSet, PaymentViewSet

app_name = "payments_api_v1"

router = SimpleRouter()
router.register("methods", PaymentMethodViewSet, basename="payment-methods")
router.register("", PaymentViewSet, basename="payments")

urlpatterns = router.urls
