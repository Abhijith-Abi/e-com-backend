from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from apps.banners.api_v1.serializers import BannerSerializer, TestimonialSerializer
from apps.banners.repositories import BannerRepository, TestimonialRepository
from core.permissions import IsAdminOrReadOnly, IsWarehouseAdminOrAdmin

BANNER_FILTER_PARAMS = [
    OpenApiParameter("device", description="Filter by device (mobile, desktop, both)", required=False),
    OpenApiParameter("status", description="Filter by status (active, inactive)", required=False),
    OpenApiParameter("search", description="Search by headline_en, headline_ar", required=False),
    OpenApiParameter("ordering", description="Order by: created_at", required=False),
]


@extend_schema_view(
    list=extend_schema(tags=["Warehouse Banners"], summary="List banners for a warehouse (Public)", parameters=BANNER_FILTER_PARAMS),
    create=extend_schema(tags=["Warehouse Banners"], summary="Create a banner in this warehouse"),
    retrieve=extend_schema(tags=["Warehouse Banners"], summary="Get a banner (Public)"),
    update=extend_schema(tags=["Warehouse Banners"], summary="Update a banner"),
    partial_update=extend_schema(tags=["Warehouse Banners"], summary="Partially update a banner"),
    destroy=extend_schema(tags=["Warehouse Banners"], summary="Delete a banner"),
)
class WarehouseScopedBannerViewSet(viewsets.ModelViewSet):
    serializer_class = BannerSerializer
    filterset_fields = ("device", "status")
    search_fields = ("headline_en", "headline_ar")
    ordering_fields = ("created_at",)

    def get_permissions(self):
        """
        Allow public access for GET requests (list, retrieve)
        Require admin authentication for POST, PUT, PATCH, DELETE
        """
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsWarehouseAdminOrAdmin()]

    def get_queryset(self):
        warehouse_id = self.kwargs.get('warehouse_id')
        if warehouse_id:
            return BannerRepository.list_banners_by_warehouse(warehouse_id)
        if hasattr(self.request, "warehouse") and self.request.warehouse:
            return BannerRepository.list_banners_by_warehouse(self.request.warehouse.id)
        return BannerRepository.list_banners().none()

    def perform_create(self, serializer):
        serializer.save(warehouse=self.request.warehouse)


@extend_schema_view(
    list=extend_schema(tags=["Banners"], summary="List all banners (Public)", parameters=BANNER_FILTER_PARAMS),
    create=extend_schema(tags=["Banners"], summary="Create a banner"),
    retrieve=extend_schema(tags=["Banners"], summary="Get a banner"),
    update=extend_schema(tags=["Banners"], summary="Update a banner"),
    partial_update=extend_schema(tags=["Banners"], summary="Partially update a banner"),
    destroy=extend_schema(tags=["Banners"], summary="Delete a banner"),
)
class BannerViewSet(viewsets.ModelViewSet):
    serializer_class = BannerSerializer
    permission_classes = [AllowAny]
    filterset_fields = ("device", "status")
    search_fields = ("headline_en", "headline_ar")
    ordering_fields = ("created_at",)

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAdminOrReadOnly()]

    def get_queryset(self):
        # Return all non-deleted banners; filtering is handled by filterset_fields
        return BannerRepository.list_banners().filter(is_deleted=False)


@extend_schema_view(
    list=extend_schema(tags=["Warehouse Testimonials"], summary="List testimonials for a warehouse"),
    create=extend_schema(tags=["Warehouse Testimonials"], summary="Create a testimonial"),
    retrieve=extend_schema(tags=["Warehouse Testimonials"], summary="Get a testimonial"),
    update=extend_schema(tags=["Warehouse Testimonials"], summary="Update a testimonial"),
    partial_update=extend_schema(tags=["Warehouse Testimonials"], summary="Partially update a testimonial"),
    destroy=extend_schema(tags=["Warehouse Testimonials"], summary="Delete a testimonial"),
)
class WarehouseScopedTestimonialViewSet(viewsets.ModelViewSet):
    serializer_class = TestimonialSerializer
    permission_classes = [IsWarehouseAdminOrAdmin]
    search_fields = ("name_en", "name_ar", "city_en", "city_ar")
    ordering_fields = ("created_at",)
    filterset_fields = ("status",)

    def get_queryset(self):
        if not hasattr(self.request, "warehouse") or not self.request.warehouse:
            return TestimonialRepository.list_testimonials().none()
        return TestimonialRepository.list_all_testimonials_by_warehouse(self.request.warehouse.id)

    def perform_create(self, serializer):
        serializer.save(warehouse=self.request.warehouse)


@extend_schema_view(
    list=extend_schema(tags=["Testimonials"], summary="List all testimonials"),
    create=extend_schema(tags=["Testimonials"], summary="Create a testimonial"),
    retrieve=extend_schema(tags=["Testimonials"], summary="Get a testimonial"),
    update=extend_schema(tags=["Testimonials"], summary="Update a testimonial"),
    partial_update=extend_schema(tags=["Testimonials"], summary="Partially update a testimonial"),
    destroy=extend_schema(tags=["Testimonials"], summary="Delete a testimonial"),
)
class TestimonialViewSet(viewsets.ModelViewSet):
    serializer_class = TestimonialSerializer
    queryset = TestimonialRepository.list_testimonials()
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = None
    search_fields = ("name_en", "name_ar", "city_en", "city_ar")
    ordering_fields = ("created_at",)
    filterset_fields = ("status",)
