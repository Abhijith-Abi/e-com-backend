from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from apps.gift_cards.api_v1.serializers import (
    GiftCardCategorySerializer,
    GiftCardSerializer,
    GiftCardWrapSerializer,
)
from apps.gift_cards.repositories import (
    GiftCardCategoryRepository,
    GiftCardRepository,
    GiftCardWrapRepository,
)
from core.permissions import IsWarehouseAdminOrAdmin

# ─── Shared filter param lists ────────────────────────────────────────────────

CATEGORY_FILTER_PARAMS = [
    OpenApiParameter("search", description="Search by name", required=False),
    OpenApiParameter("ordering", description="Order by: name, created_at", required=False),
]

WRAP_FILTER_PARAMS = [
    OpenApiParameter("status", description="Filter by status (active, inactive)", required=False),
    OpenApiParameter("search", description="Search by wrap_name", required=False),
    OpenApiParameter("ordering", description="Order by: wrap_name, created_at", required=False),
]

GIFT_CARD_FILTER_PARAMS = [
    OpenApiParameter("status", description="Filter by status (active, inactive)", required=False),
    OpenApiParameter("category", description="Filter by category UUID", required=False),
    OpenApiParameter("search", description="Search by card_name", required=False),
    OpenApiParameter("ordering", description="Order by: card_name, created_at", required=False),
]


# ─── Gift Card Category ────────────────────────────────────────────────────────

@extend_schema_view(
    list=extend_schema(
        tags=["Warehouse Gift Card Categories"],
        summary="List gift card categories for a warehouse",
        parameters=CATEGORY_FILTER_PARAMS,
    ),
    create=extend_schema(tags=["Warehouse Gift Card Categories"], summary="Create a gift card category"),
    retrieve=extend_schema(tags=["Warehouse Gift Card Categories"], summary="Get a gift card category"),
    update=extend_schema(tags=["Warehouse Gift Card Categories"], summary="Update a gift card category"),
    partial_update=extend_schema(tags=["Warehouse Gift Card Categories"], summary="Partially update a gift card category"),
    destroy=extend_schema(tags=["Warehouse Gift Card Categories"], summary="Delete a gift card category"),
)
class WarehouseScopedGiftCardCategoryViewSet(viewsets.ModelViewSet):
    serializer_class = GiftCardCategorySerializer
    search_fields = ("name",)
    ordering_fields = ("name", "created_at")

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        return [IsWarehouseAdminOrAdmin()]

    def get_queryset(self):
        if not hasattr(self.request, "warehouse") or not self.request.warehouse:
            return GiftCardCategoryRepository.list_categories().none()
        return GiftCardCategoryRepository.list_categories_by_warehouse(self.request.warehouse.id)

    def perform_create(self, serializer):
        serializer.save(warehouse=self.request.warehouse)


# ─── Gift Card Wrap ────────────────────────────────────────────────────────────

@extend_schema_view(
    list=extend_schema(
        tags=["Warehouse Gift Card Wraps"],
        summary="List gift card wraps for a warehouse",
        parameters=WRAP_FILTER_PARAMS,
    ),
    create=extend_schema(tags=["Warehouse Gift Card Wraps"], summary="Create a gift card wrap"),
    retrieve=extend_schema(tags=["Warehouse Gift Card Wraps"], summary="Get a gift card wrap"),
    update=extend_schema(tags=["Warehouse Gift Card Wraps"], summary="Update a gift card wrap"),
    partial_update=extend_schema(tags=["Warehouse Gift Card Wraps"], summary="Partially update a gift card wrap"),
    destroy=extend_schema(tags=["Warehouse Gift Card Wraps"], summary="Delete a gift card wrap"),
)
class WarehouseScopedGiftCardWrapViewSet(viewsets.ModelViewSet):
    serializer_class = GiftCardWrapSerializer
    filterset_fields = ("status",)
    search_fields = ("wrap_name",)
    ordering_fields = ("wrap_name", "created_at")

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        return [IsWarehouseAdminOrAdmin()]

    def get_queryset(self):
        if not hasattr(self.request, "warehouse") or not self.request.warehouse:
            return GiftCardWrapRepository.list_wraps().none()
        return GiftCardWrapRepository.list_wraps_by_warehouse(self.request.warehouse.id)

    def perform_create(self, serializer):
        serializer.save(warehouse=self.request.warehouse)


# ─── Gift Card ─────────────────────────────────────────────────────────────────

@extend_schema_view(
    list=extend_schema(
        tags=["Warehouse Gift Cards"],
        summary="List gift cards for a warehouse",
        parameters=GIFT_CARD_FILTER_PARAMS,
    ),
    create=extend_schema(tags=["Warehouse Gift Cards"], summary="Create a gift card"),
    retrieve=extend_schema(tags=["Warehouse Gift Cards"], summary="Get a gift card"),
    update=extend_schema(tags=["Warehouse Gift Cards"], summary="Update a gift card"),
    partial_update=extend_schema(tags=["Warehouse Gift Cards"], summary="Partially update a gift card"),
    destroy=extend_schema(tags=["Warehouse Gift Cards"], summary="Delete a gift card"),
)
class WarehouseScopedGiftCardViewSet(viewsets.ModelViewSet):
    serializer_class = GiftCardSerializer
    filterset_fields = ("status", "category")
    search_fields = ("card_name",)
    ordering_fields = ("card_name", "created_at")

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        return [IsWarehouseAdminOrAdmin()]

    def get_queryset(self):
        if not hasattr(self.request, "warehouse") or not self.request.warehouse:
            return GiftCardRepository.list_gift_cards().none()
        return GiftCardRepository.list_gift_cards_by_warehouse(self.request.warehouse.id)

    def perform_create(self, serializer):
        serializer.save(warehouse=self.request.warehouse)
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, status
from apps.gift_cards.models import LowStockGiftCardNotification, LowStockGiftCardWrapNotification
from apps.gift_cards.api_v1.serializers import LowStockGiftCardNotificationSerializer, LowStockGiftCardWrapNotificationSerializer
from core.permissions import IsWarehouseAdminOrAdmin

@extend_schema(tags=["Gift Card Notifications"], summary="Low stock gift card notifications")
class GiftCardNotificationViewSet(viewsets.ModelViewSet):
    serializer_class = LowStockGiftCardNotificationSerializer
    permission_classes = [IsWarehouseAdminOrAdmin]
    http_method_names = ["get", "patch", "delete"]

    def get_queryset(self):
        qs = LowStockGiftCardNotification.objects.select_related("gift_card").order_by("-notified_at")
        is_read = self.request.query_params.get("is_read")
        if is_read is not None:
            qs = qs.filter(is_read=is_read.lower() == "true")
        return qs

    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request):
        LowStockGiftCardNotification.objects.filter(is_read=False).update(is_read=True)
        return Response({"detail": "All marked as read."})

    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        count = LowStockGiftCardNotification.objects.filter(is_read=False).count()
        return Response({"unread_count": count})


@extend_schema(tags=["Gift Card Notifications"], summary="Low stock gift card wrap notifications")
class GiftCardWrapNotificationViewSet(viewsets.ModelViewSet):
    serializer_class = LowStockGiftCardWrapNotificationSerializer
    permission_classes = [IsWarehouseAdminOrAdmin]
    http_method_names = ["get", "patch", "delete"]

    def get_queryset(self):
        qs = LowStockGiftCardWrapNotification.objects.select_related("gift_card_wrap").order_by("-notified_at")
        is_read = self.request.query_params.get("is_read")
        if is_read is not None:
            qs = qs.filter(is_read=is_read.lower() == "true")
        return qs

    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request):
        LowStockGiftCardWrapNotification.objects.filter(is_read=False).update(is_read=True)
        return Response({"detail": "All marked as read."})

    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        count = LowStockGiftCardWrapNotification.objects.filter(is_read=False).count()
        return Response({"unread_count": count})
