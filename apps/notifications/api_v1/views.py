from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from django.db.models import Q
from core.permissions import IsWarehouseAdminOrAdmin
from apps.products.models import LowStockNotification
from apps.gift_cards.models import LowStockGiftCardNotification, LowStockGiftCardWrapNotification


@extend_schema(tags=["Notifications"], summary="Unified notifications (products, gift cards, wraps)")
class UnifiedNotificationViewSet(viewsets.ViewSet):
    permission_classes = [IsWarehouseAdminOrAdmin]

    def list(self, request):
        """Get all notifications from all sources"""
        notification_type = request.query_params.get("type")  # "product", "giftcard", "wrap", or all
        is_read = request.query_params.get("is_read")
        
        notifications = []
        
        # Product notifications
        if not notification_type or notification_type == "product":
            qs = LowStockNotification.objects.select_related("product").order_by("-notified_at")
            if is_read is not None:
                qs = qs.filter(is_read=is_read.lower() == "true")
            for notif in qs:
                notifications.append({
                    "id": str(notif.id),
                    "type": "product",
                    "title": f"Low Stock: {notif.product.name_en}",
                    "message": notif.message,
                    "is_read": notif.is_read,
                    "notified_at": notif.notified_at,
                    "product_id": str(notif.product.id),
                    "remaining_stock": notif.remaining_stock,
                    "threshold": notif.threshold,
                })
        
        # Gift Card notifications
        if not notification_type or notification_type == "giftcard":
            qs = LowStockGiftCardNotification.objects.select_related("gift_card").order_by("-notified_at")
            if is_read is not None:
                qs = qs.filter(is_read=is_read.lower() == "true")
            for notif in qs:
                notifications.append({
                    "id": str(notif.id),
                    "type": "giftcard",
                    "title": f"Low Stock: {notif.gift_card.card_name}",
                    "message": notif.message,
                    "is_read": notif.is_read,
                    "notified_at": notif.notified_at,
                    "gift_card_id": str(notif.gift_card.id),
                    "remaining_units": notif.remaining_units,
                    "threshold": notif.threshold,
                })
        
        # Gift Card Wrap notifications
        if not notification_type or notification_type == "wrap":
            qs = LowStockGiftCardWrapNotification.objects.select_related("gift_card_wrap").order_by("-notified_at")
            if is_read is not None:
                qs = qs.filter(is_read=is_read.lower() == "true")
            for notif in qs:
                notifications.append({
                    "id": str(notif.id),
                    "type": "wrap",
                    "title": f"Low Stock: {notif.gift_card_wrap.wrap_name}",
                    "message": notif.message,
                    "is_read": notif.is_read,
                    "notified_at": notif.notified_at,
                    "wrap_id": str(notif.gift_card_wrap.id),
                    "remaining_units": notif.remaining_units,
                    "threshold": notif.threshold,
                })
        
        # Sort by date (newest first)
        notifications.sort(key=lambda x: x["notified_at"], reverse=True)
        return Response(notifications)

    @extend_schema(summary="Mark all notifications as read")
    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request):
        LowStockNotification.objects.filter(is_read=False).update(is_read=True)
        LowStockGiftCardNotification.objects.filter(is_read=False).update(is_read=True)
        LowStockGiftCardWrapNotification.objects.filter(is_read=False).update(is_read=True)
        return Response({"detail": "All notifications marked as read."})

    @extend_schema(summary="Get unread notification count")
    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        count = (
            LowStockNotification.objects.filter(is_read=False).count() +
            LowStockGiftCardNotification.objects.filter(is_read=False).count() +
            LowStockGiftCardWrapNotification.objects.filter(is_read=False).count()
        )
        return Response({"unread_count": count})
