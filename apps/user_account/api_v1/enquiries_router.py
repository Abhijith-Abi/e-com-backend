from rest_framework.routers import SimpleRouter

from apps.user_account.api_v1.views import EnquiryViewSet

router = SimpleRouter()
router.register("", EnquiryViewSet, basename="enquiry")

urlpatterns = router.urls
