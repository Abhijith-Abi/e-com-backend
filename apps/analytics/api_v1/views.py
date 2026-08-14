from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import viewsets

from apps.analytics.api_v1.serializers import StoreAnalyticsSerializer
from apps.analytics.repositories import AnalyticsRepository
from core.permissions import IsAdminOrReadOnly


@extend_schema_view(
    list=extend_schema(
        tags=["Analytics"],
        summary="List store analytics records",
        parameters=[
            OpenApiParameter("ordering", description="Order by: created_at, total_revenue, total_orders", required=False),
        ],
    ),
    create=extend_schema(tags=["Analytics"], summary="Create an analytics record"),
    retrieve=extend_schema(tags=["Analytics"], summary="Get an analytics record"),
    update=extend_schema(tags=["Analytics"], summary="Update an analytics record"),
    partial_update=extend_schema(tags=["Analytics"], summary="Partially update an analytics record"),
    destroy=extend_schema(tags=["Analytics"], summary="Delete an analytics record"),
)
class StoreAnalyticsViewSet(viewsets.ModelViewSet):
    serializer_class = StoreAnalyticsSerializer
    queryset = AnalyticsRepository.list_analytics()
    permission_classes = [IsAdminOrReadOnly]
    ordering_fields = ("created_at", "total_revenue", "total_orders")
