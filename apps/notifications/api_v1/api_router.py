from django.urls import path
from rest_framework.routers import SimpleRouter
from apps.notifications.api_v1.views import UnifiedNotificationViewSet

app_name = "notifications_api_v1"

router = SimpleRouter()
router.register("", UnifiedNotificationViewSet, basename="notifications")

urlpatterns = router.urls
