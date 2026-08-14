from rest_framework.routers import SimpleRouter

from apps.banners.api_v1.views import WarehouseScopedBannerViewSet, WarehouseScopedTestimonialViewSet

app_name = "warehouse_banners_api_v1"

router = SimpleRouter()
router.register("banners", WarehouseScopedBannerViewSet, basename="warehouse-banners")
router.register("testimonials", WarehouseScopedTestimonialViewSet, basename="warehouse-testimonials")

urlpatterns = router.urls
