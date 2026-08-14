from rest_framework.routers import SimpleRouter

from apps.banners.api_v1.views import BannerViewSet, TestimonialViewSet

app_name = "banners_api_v1"

router = SimpleRouter()
router.register("banners", BannerViewSet, basename="banners")
router.register("testimonials", TestimonialViewSet, basename="testimonials")

urlpatterns = router.urls
