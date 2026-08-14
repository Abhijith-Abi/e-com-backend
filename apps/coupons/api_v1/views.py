from decimal import Decimal

from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import permissions, status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.coupons.api_v1.serializers import (
    ApplyCouponRequestSerializer,
    ApplyCouponResponseSerializer,
    CouponSerializer,
    OfferSerializer,
)
from apps.coupons.repositories import CouponRepository, OfferRepository
from apps.coupons.services import CouponService
from core.permissions import IsAdminOrReadOnly, IsWarehouseAdminOrAdmin
from rest_framework.pagination import PageNumberPagination


import django_filters
from django.utils import timezone
from apps.coupons.models import Coupon

class CouponFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(method="filter_by_status")

    class Meta:
        model = Coupon
        fields = ("region", "coupon_type")

    def filter_by_status(self, queryset, name, value):
        now = timezone.now()
        value = value.lower()
        from django.db.models import F, Q
        if value == "active":
            return queryset.filter(
                status="active",
                valid_until__gte=now
            ).filter(
                Q(usage_limit__isnull=True) | Q(actual_usage__lt=F("usage_limit"))
            )
        elif value == "expired":
            return queryset.filter(status="active", valid_until__lt=now)
        elif value == "usage_exceeded":
            return queryset.filter(
                status="active",
                usage_limit__isnull=False,
                actual_usage__gte=F("usage_limit")
            )
        elif value == "inactive":
            return queryset.filter(status="inactive")
        return queryset


class OfferPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


@extend_schema_view(
    list=extend_schema(
        tags=["Coupons"],
        summary="List coupons",
        parameters=[
            OpenApiParameter("region", description="Filter by region (INDIA, UAE, UK)", required=False),
            OpenApiParameter("status", description="Filter by status (active, inactive, expired, usage_exceeded)", required=False),
            OpenApiParameter("coupon_type", description="Filter by type (percentage, fixed)", required=False),
            OpenApiParameter("search", description="Search by coupon_code", required=False),
            OpenApiParameter("ordering", description="Order by: created_at, valid_until, coupon_value", required=False),
        ],
    ),
    create=extend_schema(tags=["Coupons"], summary="Create a coupon"),
    retrieve=extend_schema(tags=["Coupons"], summary="Get a coupon"),
    update=extend_schema(tags=["Coupons"], summary="Update a coupon"),
    partial_update=extend_schema(tags=["Coupons"], summary="Partially update a coupon"),
    destroy=extend_schema(tags=["Coupons"], summary="Delete a coupon"),
)
class CouponViewSet(viewsets.ModelViewSet):
    serializer_class = CouponSerializer
    queryset = CouponRepository.list_coupons()
    permission_classes = [IsAdminOrReadOnly]
    filterset_class = CouponFilter
    search_fields = ("coupon_code",)
    ordering_fields = ("created_at", "valid_until", "coupon_value")


OFFER_FILTER_PARAMS = [
    OpenApiParameter("status", description="Filter by status (active, inactive)", required=False),
    OpenApiParameter("search", description="Search by heading_en, heading_ar", required=False),
    OpenApiParameter("ordering", description="Order by: created_at", required=False),
]


@extend_schema_view(
    list=extend_schema(tags=["Warehouse Offers"], summary="List offers for a warehouse", parameters=OFFER_FILTER_PARAMS),
    create=extend_schema(tags=["Warehouse Offers"], summary="Create an offer in this warehouse"),
    retrieve=extend_schema(tags=["Warehouse Offers"], summary="Get an offer"),
    update=extend_schema(tags=["Warehouse Offers"], summary="Update an offer"),
    partial_update=extend_schema(tags=["Warehouse Offers"], summary="Partially update an offer"),
    destroy=extend_schema(tags=["Warehouse Offers"], summary="Delete an offer"),
)
class WarehouseScopedOfferViewSet(viewsets.ModelViewSet):
    serializer_class = OfferSerializer
    filterset_fields = ("status",)
    search_fields = ("heading_en", "heading_ar")
    ordering_fields = ("created_at",)
    pagination_class = OfferPagination

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        return [IsWarehouseAdminOrAdmin()]

    def get_queryset(self):
        if not hasattr(self.request, "warehouse") or not self.request.warehouse:
            return OfferRepository.list_offers().none()
        return OfferRepository.list_offers_by_warehouse(self.request.warehouse.id)

    def perform_create(self, serializer):
        serializer.save(warehouse=self.request.warehouse)


@extend_schema_view(
    list=extend_schema(tags=["Offers"], summary="List all offers", parameters=OFFER_FILTER_PARAMS),
    create=extend_schema(tags=["Offers"], summary="Create an offer"),
    retrieve=extend_schema(tags=["Offers"], summary="Get an offer"),
    update=extend_schema(tags=["Offers"], summary="Update an offer"),
    partial_update=extend_schema(tags=["Offers"], summary="Partially update an offer"),
    destroy=extend_schema(tags=["Offers"], summary="Delete an offer"),
)
class OfferViewSet(viewsets.ModelViewSet):
    serializer_class = OfferSerializer
    queryset = OfferRepository.list_offers()
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ("status", "warehouse")
    search_fields = ("heading_en", "heading_ar")
    ordering_fields = ("created_at",)
    pagination_class = OfferPagination

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        return super().get_permissions()


@extend_schema(
    tags=["Coupons"],
    summary="Apply a coupon",
    description=(
        "Validates a coupon code for the given region and amount, "
        "then returns the discounted total and discount breakdown.\n\n"
        "Can also be called under `/warehouses/{warehouse_id}/apply-coupon/` "
        "where the warehouse is automatically resolved from the URL."
    ),
    request=ApplyCouponRequestSerializer,
    responses={200: ApplyCouponResponseSerializer},
)
class ApplyCouponView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, warehouse_id=None):
        serializer = ApplyCouponRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data["coupon_code"]
        region = serializer.validated_data["region"]
        amount = Decimal(str(serializer.validated_data["amount"]))

        # Resolve warehouse: from URL path > request.warehouse (middleware) > body
        warehouse = None
        if warehouse_id:
            from apps.warehouses.models import Warehouse
            warehouse = Warehouse.objects.filter(pk=warehouse_id).first()
            if not warehouse:
                return Response({"detail": "Warehouse not found."}, status=status.HTTP_404_NOT_FOUND)
        elif hasattr(request, "warehouse") and request.warehouse:
            warehouse = request.warehouse
        elif serializer.validated_data.get("warehouse_id"):
            from apps.warehouses.models import Warehouse
            warehouse = Warehouse.objects.filter(pk=serializer.validated_data["warehouse_id"]).first()
            if not warehouse:
                return Response({"detail": "Warehouse not found."}, status=status.HTTP_404_NOT_FOUND)

        # Get customer profile for per-user validation
        customer = None
        if hasattr(request.user, 'customer_profile'):
            customer = request.user.customer_profile

        coupon = CouponRepository.get_valid_coupon(code, region, customer=customer)
        if not coupon:
            return Response(
                {"detail": "Invalid, expired, or already used coupon code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from core.choices import CouponTypeChoices
        if coupon.coupon_type == CouponTypeChoices.FIXED and coupon.coupon_value >= amount:
            return Response(
                {"detail": "Coupon discount cannot be greater than or equal to the total amount."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        discounted_amount = CouponService.apply_discount(coupon, amount)
        discount_applied = amount - discounted_amount

        response_data = {
            "coupon_code": coupon.coupon_code,
            "coupon_type": coupon.coupon_type,
            "coupon_value": coupon.coupon_value,
            "original_amount": amount,
            "discounted_amount": discounted_amount,
            "discount_applied": discount_applied,
        }
        if warehouse:
            response_data["warehouse_id"] = str(warehouse.id)

        response = ApplyCouponResponseSerializer(response_data)
        return Response(response.data, status=status.HTTP_200_OK)
