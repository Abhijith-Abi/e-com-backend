from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import permissions, viewsets

from apps.couriers.api_v1.serializers import CourierSerializer
from apps.couriers.repositories import CourierRepository
from core.permissions import IsWarehouseAdminOrAdmin


@extend_schema_view(
    list=extend_schema(
        tags=["Warehouse Couriers"],
        summary="List couriers for a warehouse",
        parameters=[
            OpenApiParameter("search", description="Search by name, courier_number", required=False),
            OpenApiParameter("ordering", description="Order by: created_at", required=False),
        ],
    ),
    create=extend_schema(tags=["Warehouse Couriers"], summary="Create a courier"),
    retrieve=extend_schema(tags=["Warehouse Couriers"], summary="Get a courier"),
    update=extend_schema(tags=["Warehouse Couriers"], summary="Update a courier"),
    partial_update=extend_schema(tags=["Warehouse Couriers"], summary="Partially update a courier"),
    destroy=extend_schema(tags=["Warehouse Couriers"], summary="Delete a courier"),
)
class WarehouseScopedCourierViewSet(viewsets.ModelViewSet):
    serializer_class = CourierSerializer
    search_fields = ("name", "courier_number")
    ordering_fields = ("created_at",)

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        return [IsWarehouseAdminOrAdmin()]

    def get_queryset(self):
        if not hasattr(self.request, "warehouse") or not self.request.warehouse:
            return CourierRepository.list_couriers().none()
        return CourierRepository.list_couriers().filter(warehouse=self.request.warehouse)

    def perform_create(self, serializer):
        serializer.save(warehouse=self.request.warehouse)
