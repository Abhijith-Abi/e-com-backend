from rest_framework.routers import SimpleRouter

from apps.categories.api_v1.views import CategoryViewSet

app_name = "categories_api_v1"

router = SimpleRouter()
router.register("", CategoryViewSet, basename="categories")

urlpatterns = router.urls

