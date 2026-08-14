from rest_framework.routers import SimpleRouter

from apps.cart.api_v1.views import CartItemViewSet, CartViewSet

app_name = "cart_api_v1"

router = SimpleRouter()
router.register("carts", CartViewSet, basename="carts")
router.register("items", CartItemViewSet, basename="cart-items")

urlpatterns = router.urls

