from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, permissions, viewsets

from apps.payments.api_v1.serializers import PaymentMethodSerializer, PaymentSerializer
from apps.payments.models import PaymentMethod
from apps.payments.repositories import PaymentRepository


@extend_schema_view(
    list=extend_schema(tags=["Payment Methods"], summary="List active payment methods"),
    retrieve=extend_schema(tags=["Payment Methods"], summary="Get a payment method"),
    create=extend_schema(tags=["Payment Methods"], summary="Create a payment method (admin)"),
    update=extend_schema(tags=["Payment Methods"], summary="Update a payment method (admin)"),
    partial_update=extend_schema(tags=["Payment Methods"], summary="Partially update a payment method (admin)"),
    destroy=extend_schema(tags=["Payment Methods"], summary="Remove a payment method (admin)"),
)
class PaymentMethodViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentMethodSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.is_staff:
            return PaymentMethod.objects.all()
        return PaymentMethod.objects.filter(is_active=True)

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]


@extend_schema_view(
    list=extend_schema(
        tags=["Payments"],
        summary="List payments",
        parameters=[
            OpenApiParameter("payment_method", description="Filter by payment method UUID", required=False),
            OpenApiParameter("payment_status", description="Filter by status (pending, authorized, paid, failed, refunded)", required=False),
            OpenApiParameter("order", description="Filter by order UUID", required=False),
            OpenApiParameter("search", description="Search by transaction_id, order__order_id", required=False),
            OpenApiParameter("ordering", description="Order by: created_at", required=False),
        ],
    ),
    create=extend_schema(tags=["Payments"], summary="Create a payment record"),
    retrieve=extend_schema(tags=["Payments"], summary="Get a payment"),
    update=extend_schema(tags=["Payments"], summary="Update a payment"),
    partial_update=extend_schema(tags=["Payments"], summary="Partially update a payment"),
    destroy=extend_schema(tags=["Payments"], summary="Delete a payment"),
)
class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    queryset = PaymentRepository.list_payments()
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ("payment_method", "payment_status", "order")
    search_fields = ("transaction_id", "order__order_id")
    ordering_fields = ("created_at",)

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(order__customer__user=self.request.user)
