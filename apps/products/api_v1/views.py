from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.products.api_v1.filters import ProductFilter
from apps.products.api_v1.serializers import (
    BestSellerProductSerializer,
    BulkProductImageSerializer,
    NewProductSerializer,
    ProductImageSerializer,
    ProductSerializer,
    WarehouseScopedProductSerializer,
)
from apps.products.repositories import ProductImageRepository, ProductRepository
from core.choices import ProductStatusChoices, ProductTypeChoices
from core.permissions import IsAdminOrReadOnly, IsWarehouseAdminOrAdmin
from django.db.models import ProtectedError


@extend_schema_view(
    list=extend_schema(
        tags=["Warehouse Products"],
        summary="List products in a warehouse",
        parameters=[
            OpenApiParameter("category", description="Filter by category UUID", required=False),
            OpenApiParameter("category_name", description="Filter by category name (starts with, e.g. 'jewellery')", required=False),
            OpenApiParameter("sub_category", description="Filter by sub-category UUID", required=False),
            OpenApiParameter("status", description="Filter by status", required=False),
            OpenApiParameter("is_featured", description="Filter featured products (true/false)", required=False),
            OpenApiParameter("type", description="Filter by type (physical, digital)", required=False),
            OpenApiParameter("tag", description="Filter by category or sub-category name (exact case-insensitive)", required=False),
            OpenApiParameter("search", description="Search by name_en, name_ar, sku", required=False),
            OpenApiParameter("ordering", description="Order by: created_at, price_inr, price_gbp, price_usd, stock, popularity", required=False),
        ],
    ),
    create=extend_schema(tags=["Warehouse Products"], summary="Create a product in this warehouse"),
    retrieve=extend_schema(tags=["Warehouse Products"], summary="Get a product"),
    update=extend_schema(tags=["Warehouse Products"], summary="Update a product"),
    partial_update=extend_schema(tags=["Warehouse Products"], summary="Partially update a product"),
    destroy=extend_schema(tags=["Warehouse Products"], summary="Delete a product"),
)
class WarehouseScopedProductViewSet(viewsets.ModelViewSet):
    """
    Products scoped to a warehouse. warehouse is resolved from the URL by WarehouseScopingMiddleware.
    Product name (name_en) must be unique within the same warehouse.
    """
    serializer_class = WarehouseScopedProductSerializer
    filterset_class = ProductFilter
    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsWarehouseAdminOrAdmin()]
    search_fields = ("name_en", "name_ar", "sku")
    ordering_fields = ("created_at", "price_inr", "price_gbp", "price_usd", "stock", "popularity")
    ordering = ("-created_at",)

    def get_queryset(self):
        if not hasattr(self.request, "warehouse") or not self.request.warehouse:
            return ProductRepository.list_products().none()
        from django.db.models import Sum
        from django.db.models.functions import Coalesce
        return ProductRepository.list_products_by_warehouse(self.request.warehouse.id).annotate(
            actual_price_inr=Coalesce("sale_price_inr", "price_inr"),
            actual_price_gbp=Coalesce("sale_price_gbp", "price_gbp"),
            actual_price_usd=Coalesce("sale_price_usd", "price_usd"),
            popularity=Coalesce(Sum("order_items__quantity"), 0)
        )

    def filter_queryset(self, queryset):
        # Remove OrderingFilter from filter backends to apply custom ordering logic
        backends = [b for b in self.filter_backends if b.__name__ != "OrderingFilter"]
        
        # Apply remaining filters (DjangoFilterBackend, SearchFilter)
        for backend in backends:
            queryset = backend().filter_queryset(self.request, queryset, self)
            
        # Apply custom ordering mapping
        ordering = self.request.query_params.get("ordering", "")
        if ordering:
            params = [p.strip() for p in ordering.split(",")]
            order_by_fields = []
            for p in params:
                desc = p.startswith("-")
                field = p.lstrip("-")
                if field == "price_inr":
                    order_by_fields.append("-actual_price_inr" if desc else "actual_price_inr")
                elif field == "price_gbp":
                    order_by_fields.append("-actual_price_gbp" if desc else "actual_price_gbp")
                elif field == "price_usd":
                    order_by_fields.append("-actual_price_usd" if desc else "actual_price_usd")
                elif field == "popularity":
                    order_by_fields.append("-popularity" if desc else "popularity")
                elif field in ["created_at", "stock"]:
                    order_by_fields.append("-" + field if desc else field)
            if order_by_fields:
                queryset = queryset.order_by(*order_by_fields)
        else:
            queryset = queryset.order_by("-created_at")
            
        return queryset

    def perform_create(self, serializer):
        serializer.save(warehouse=self.request.warehouse)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            instance.delete()
        except ProtectedError:
            return Response(
                {"detail": "Cannot delete this product because it is linked to existing orders."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    list=extend_schema(
        tags=["Products"],
        summary="List all products",
        parameters=[
            OpenApiParameter("category", description="Filter by category UUID", required=False),
            OpenApiParameter("sub_category", description="Filter by sub-category UUID", required=False),
            OpenApiParameter("status", description="Filter by status", required=False),
            OpenApiParameter("is_featured", description="Filter featured products (true/false)", required=False),
            OpenApiParameter("type", description="Filter by type (physical, digital)", required=False),
            OpenApiParameter("warehouse", description="Filter by warehouse UUID", required=False),
            OpenApiParameter("tag", description="Filter by category or sub-category name (exact case-insensitive)", required=False),
            OpenApiParameter("search", description="Search by name_en, name_ar, sku", required=False),
            OpenApiParameter("ordering", description="Order by: created_at, price_inr, price_gbp, price_usd, stock, popularity", required=False),
        ],
    ),
    create=extend_schema(tags=["Products"], summary="Create a product"),
    retrieve=extend_schema(tags=["Products"], summary="Get a product"),
    update=extend_schema(tags=["Products"], summary="Update a product"),
    partial_update=extend_schema(tags=["Products"], summary="Partially update a product"),
    destroy=extend_schema(tags=["Products"], summary="Delete a product"),
)
class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAdminOrReadOnly()]
    
    def get_queryset(self):
        from django.db.models import Sum
        from django.db.models.functions import Coalesce
        return ProductRepository.list_products().annotate(
            actual_price_inr=Coalesce("sale_price_inr", "price_inr"),
            actual_price_gbp=Coalesce("sale_price_gbp", "price_gbp"),
            actual_price_usd=Coalesce("sale_price_usd", "price_usd"),
            popularity=Coalesce(Sum("order_items__quantity"), 0)
        )

    def filter_queryset(self, queryset):
        # Remove OrderingFilter from filter backends to apply custom ordering logic
        backends = [b for b in self.filter_backends if b.__name__ != "OrderingFilter"]
        
        # Apply remaining filters (DjangoFilterBackend, SearchFilter)
        for backend in backends:
            queryset = backend().filter_queryset(self.request, queryset, self)
            
        # Apply custom ordering mapping
        ordering = self.request.query_params.get("ordering", "")
        if ordering:
            params = [p.strip() for p in ordering.split(",")]
            order_by_fields = []
            for p in params:
                desc = p.startswith("-")
                field = p.lstrip("-")
                if field == "price_inr":
                    order_by_fields.append("-actual_price_inr" if desc else "actual_price_inr")
                elif field == "price_gbp":
                    order_by_fields.append("-actual_price_gbp" if desc else "actual_price_gbp")
                elif field == "price_usd":
                    order_by_fields.append("-actual_price_usd" if desc else "actual_price_usd")
                elif field == "popularity":
                    order_by_fields.append("-popularity" if desc else "popularity")
                elif field in ["created_at", "stock"]:
                    order_by_fields.append("-" + field if desc else field)
            if order_by_fields:
                queryset = queryset.order_by(*order_by_fields)
        else:
            queryset = queryset.order_by("-created_at")
            
        return queryset


@extend_schema_view(
    list=extend_schema(
        tags=["Products"],
        summary="List product images",
        parameters=[
            OpenApiParameter("product", description="Filter by product UUID", required=False),
            OpenApiParameter("is_primary", description="Filter primary images (true/false)", required=False),
            OpenApiParameter("color", description="Filter by color (e.g. Red, Blue)", required=False),
        ],
    ),
    create=extend_schema(tags=["Products"], summary="Upload a product image"),
    retrieve=extend_schema(tags=["Products"], summary="Get a product image"),
    update=extend_schema(tags=["Products"], summary="Update a product image"),
    partial_update=extend_schema(tags=["Products"], summary="Partially update a product image"),
    destroy=extend_schema(tags=["Products"], summary="Delete a product image"),
)
class ProductImageViewSet(viewsets.ModelViewSet):
    serializer_class = ProductImageSerializer
    permission_classes = [IsAdminOrReadOnly]
    queryset = ProductImageRepository.list_images()
    filterset_fields = ("product", "is_primary", "color")

    @extend_schema(
        tags=["Products"],
        summary="Upload multiple images for a product at once",
        request=BulkProductImageSerializer,
        responses={201: ProductImageSerializer(many=True)},
    )
    @action(detail=False, methods=["post"], url_path="bulk-upload")
    def bulk_upload(self, request):
        serializer = BulkProductImageSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        images = serializer.save()
        return Response(
            ProductImageSerializer(images, many=True, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=["Warehouse Products"],
    summary="List new products in a warehouse (last 7 days)",
    parameters=[
        OpenApiParameter("days", description="Number of days to look back (default: 7)", required=False, type=int),
        OpenApiParameter("category", description="Filter by category UUID", required=False),
        OpenApiParameter("sub_category", description="Filter by sub-category UUID", required=False),
    ],
)
class WarehouseNewProductsListView(ListAPIView):
    serializer_class = NewProductSerializer
    permission_classes = [AllowAny]
    filterset_fields = ("category", "sub_category")

    def get_queryset(self):
        warehouse = getattr(self.request, "warehouse", None)
        days = int(self.request.query_params.get("days", 7))
        qs = ProductRepository.list_new_products(days=days)
        if warehouse:
            qs = qs.filter(warehouse=warehouse)
        return qs


@extend_schema(
    tags=["Products"],
    summary="List new products (last 7 days)",
    parameters=[
        OpenApiParameter("days", description="Number of days to look back (default: 7)", required=False, type=int),
        OpenApiParameter("category", description="Filter by category UUID", required=False),
        OpenApiParameter("sub_category", description="Filter by sub-category UUID", required=False),
    ],
)
class NewProductsListView(ListAPIView):
    serializer_class = NewProductSerializer
    permission_classes = [AllowAny]
    filterset_fields = ("category", "sub_category")

    def get_queryset(self):
        days = int(self.request.query_params.get("days", 7))
        return ProductRepository.list_new_products(days=days)


@extend_schema(tags=["Products"], summary="List product types")
class ProductTypeChoicesView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response([{"value": v, "label": label} for v, label in ProductTypeChoices.choices])


@extend_schema(tags=["Products"], summary="List product statuses")
class ProductStatusChoicesView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response([{"value": v, "label": label} for v, label in ProductStatusChoices.choices])


@extend_schema(
    tags=["Warehouse Products"],
    summary="Top 10 best-selling products in a warehouse (past 2 months)",
    parameters=[
        OpenApiParameter("category", description="Filter by category UUID", required=False),
        OpenApiParameter("sub_category", description="Filter by sub-category UUID", required=False),
        OpenApiParameter("type", description="Filter by type (physical, digital)", required=False),
        OpenApiParameter("months", description="Look-back period in months (default: 2)", required=False, type=int),
        OpenApiParameter("limit", description="Number of results (default: 10, max: 50)", required=False, type=int),
    ],
)
class WarehouseBestSellersListView(ListAPIView):
    serializer_class = BestSellerProductSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        warehouse = getattr(self.request, "warehouse", None)
        if not warehouse:
            return ProductRepository.list_products().none()
        months = int(self.request.query_params.get("months", 2))
        limit = min(int(self.request.query_params.get("limit", 10)), 50)
        qs = ProductRepository.list_best_sellers_by_warehouse(warehouse.id, months=months, limit=limit)
        category = self.request.query_params.get("category")
        sub_category = self.request.query_params.get("sub_category")
        product_type = self.request.query_params.get("type")
        if category:
            qs = qs.filter(category_id=category)
        if sub_category:
            qs = qs.filter(sub_category_id=sub_category)
        if product_type:
            qs = qs.filter(type=product_type)
        return qs


from apps.products.models import LowStockNotification
from apps.products.api_v1.serializers import LowStockNotificationSerializer
from rest_framework.generics import ListAPIView
from rest_framework.decorators import action
from core.permissions import IsAdminOrReadOnly

@extend_schema(tags=["Notifications"], summary="Low stock notifications")
class LowStockNotificationViewSet(viewsets.ModelViewSet):
    serializer_class = LowStockNotificationSerializer
    permission_classes = [IsAdminOrReadOnly]
    http_method_names = ["get", "patch", "delete"]  # no POST, no PUT

    def get_queryset(self):
        is_read = self.request.query_params.get("is_read")
        qs = LowStockNotification.objects.select_related("product").order_by("-notified_at")
        if is_read is not None:
            qs = qs.filter(is_read=is_read.lower() == "true")
        return qs

    @extend_schema(summary="Mark all notifications as read")
    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request):
        LowStockNotification.objects.filter(is_read=False).update(is_read=True)
        return Response({"detail": "All notifications marked as read."})

    @extend_schema(summary="Get unread notification count")
    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        count = LowStockNotification.objects.filter(is_read=False).count()
        return Response({"unread_count": count})
