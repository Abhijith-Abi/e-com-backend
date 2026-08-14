from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import viewsets, permissions

from apps.warehouses.api_v1.serializers import WarehouseSerializer
from apps.warehouses.repositories import WarehouseRepository
from core.permissions import IsAdminOrReadOnly


@extend_schema_view(
    list=extend_schema(
        tags=["Warehouses"],
        summary="List all warehouses (Public)",
        parameters=[
            OpenApiParameter("warehouse_location", description="Filter by location (INDIA, UAE, UK)", required=False),
            OpenApiParameter("is_active", description="Filter by active status (true/false)", required=False),
            OpenApiParameter("search", description="Search by warehouse_name or warehouse_address", required=False),
            OpenApiParameter("ordering", description="Order by: warehouse_name, created_at", required=False),
        ],
    ),
    create=extend_schema(tags=["Warehouses"], summary="Create a warehouse"),
    retrieve=extend_schema(tags=["Warehouses"], summary="Get a warehouse (Public)"),
    update=extend_schema(tags=["Warehouses"], summary="Update a warehouse"),
    partial_update=extend_schema(tags=["Warehouses"], summary="Partially update a warehouse"),
    destroy=extend_schema(tags=["Warehouses"], summary="Delete a warehouse"),
)
class WarehouseViewSet(viewsets.ModelViewSet):
    serializer_class = WarehouseSerializer
    permission_classes = [IsAdminOrReadOnly]
    queryset = WarehouseRepository.list_warehouses()
    filterset_fields = ("warehouse_location", "is_active")
    search_fields = ("warehouse_name", "warehouse_address")
    ordering_fields = ("warehouse_name", "created_at")

    def get_permissions(self):
        """
        Allow public access for list and retrieve actions.
        Require admin authentication for create, update, delete.
        """
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]
