from rest_framework.routers import SimpleRouter

from apps.gift_cards.api_v1.views import (
    WarehouseScopedGiftCardCategoryViewSet,
    WarehouseScopedGiftCardViewSet,
    WarehouseScopedGiftCardWrapViewSet,
)
from apps.gift_cards.api_v1.views import GiftCardNotificationViewSet, GiftCardWrapNotificationViewSet


app_name = "warehouse_gift_cards_api_v1"

router = SimpleRouter()
router.register("categories", WarehouseScopedGiftCardCategoryViewSet, basename="warehouse-gift-card-categories")
router.register("wraps", WarehouseScopedGiftCardWrapViewSet, basename="warehouse-gift-card-wraps")
router.register("cards", WarehouseScopedGiftCardViewSet, basename="warehouse-gift-cards")
router.register("notifications/cards", GiftCardNotificationViewSet, basename="gift-card-notifications")
router.register("notifications/wraps", GiftCardWrapNotificationViewSet, basename="gift-card-wrap-notifications")

urlpatterns = router.urls
