from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response

from apps.customers.api_v1.serializers import (
    CustomerAddressSerializer,
    CustomerProfileDetailSerializer,
    CustomerProfileSerializer,
    WarehouseCustomerProfileSerializer,
    WishlistSerializer,
)
from apps.customers.models import CustomerAddress
from apps.customers.repositories import CustomerAddressRepository, CustomerRepository, WishlistRepository
from core.permissions import IsAdminOrReadOnly
from core.permissions import IsActiveCustomer


@extend_schema_view(
    list=extend_schema(
        tags=["Customers"],
        summary="List all customer profiles",
        parameters=[
            OpenApiParameter("preferred_language", description="Filter by language (en, ar)", required=False),
            OpenApiParameter("preferred_currency", description="Filter by currency (INR, GBP, USD)", required=False),
            OpenApiParameter("is_suspended", description="Filter suspended customers (true/false)", required=False),
            OpenApiParameter("search", description="Search by user__email, user__full_name", required=False),
            OpenApiParameter("ordering", description="Order by: created_at", required=False),
        ],
    ),
    create=extend_schema(tags=["Customers"], summary="Create a customer profile"),
    retrieve=extend_schema(tags=["Customers"], summary="Get a customer profile with orders and addresses"),
    update=extend_schema(tags=["Customers"], summary="Update a customer profile"),
    partial_update=extend_schema(tags=["Customers"], summary="Partially update a customer profile"),
    destroy=extend_schema(tags=["Customers"], summary="Delete a customer profile"),
)
class CustomerProfileViewSet(viewsets.ModelViewSet):
    queryset = CustomerRepository.list_profiles()
    filterset_fields = ("preferred_language", "preferred_currency", "is_suspended")
    search_fields = ("user__email", "user__full_name")
    ordering_fields = ("created_at",)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CustomerProfileDetailSerializer
        return CustomerProfileSerializer

    def get_queryset(self):
        user = self.request.user
        if self.action == "retrieve":
            qs = CustomerRepository.list_profiles_with_orders_and_addresses()
        else:
            qs = CustomerRepository.list_profiles()
        if not user.is_authenticated or not user.is_admin:
            return qs.filter(user=user)
        return qs

    def get_permissions(self):
        if self.action in ("list", "retrieve", "destroy", "update", "partial_update"):
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]


@extend_schema_view(
    list=extend_schema(
        tags=["My Addresses"],
        summary="List my addresses",
        description="Returns all saved addresses for the currently authenticated user.",
    ),
    create=extend_schema(
        tags=["My Addresses"],
        summary="Add a new address",
        description="Creates a new address for the currently authenticated user.",
    ),
    retrieve=extend_schema(tags=["My Addresses"], summary="Get an address"),
    update=extend_schema(tags=["My Addresses"], summary="Update an address"),
    partial_update=extend_schema(tags=["My Addresses"], summary="Partially update an address"),
    destroy=extend_schema(tags=["My Addresses"], summary="Delete an address"),
)
class MyAddressViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerAddressSerializer
    permission_classes = [IsActiveCustomer]

    def get_queryset(self):
        from apps.customers.services import CustomerService
        customer = CustomerService.ensure_profile(self.request.user)
        return CustomerAddress.objects.filter(customer=customer).order_by("-is_default", "-created_at")

    def perform_create(self, serializer):
        from apps.customers.services import CustomerService
        customer = CustomerService.ensure_profile(self.request.user)
        serializer.save(customer=customer)


@extend_schema_view(
    list=extend_schema(
        tags=["Customer Addresses"],
        summary="List addresses for a customer",
    ),
    create=extend_schema(tags=["Customer Addresses"], summary="Create a customer address"),
    retrieve=extend_schema(tags=["Customer Addresses"], summary="Get a customer address"),
    update=extend_schema(tags=["Customer Addresses"], summary="Update a customer address"),
    partial_update=extend_schema(tags=["Customer Addresses"], summary="Partially update a customer address"),
    destroy=extend_schema(tags=["Customer Addresses"], summary="Delete a customer address"),
)
class CustomerAddressViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerAddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        customer_id = self.kwargs.get("customer_id")
        qs = CustomerAddressRepository.list_addresses(customer_id=customer_id)
        if not self.request.user.is_admin:
            qs = qs.filter(customer__user=self.request.user)
        return qs


@extend_schema_view(
    list=extend_schema(
        tags=["Warehouse Customers"],
        summary="List customer profiles for a warehouse",
        parameters=[
            OpenApiParameter("preferred_language", description="Filter by language (en, ar)", required=False),
            OpenApiParameter("preferred_currency", description="Filter by currency (INR, GBP, USD)", required=False),
            OpenApiParameter("is_suspended", description="Filter suspended customers (true/false)", required=False),
            OpenApiParameter("search", description="Search by user__email, user__full_name", required=False),
            OpenApiParameter("ordering", description="Order by: created_at", required=False),
        ],
    ),
    retrieve=extend_schema(tags=["Warehouse Customers"], summary="Get a customer profile"),
    partial_update=extend_schema(tags=["Warehouse Customers"], summary="Partially update a customer profile"),
    update=extend_schema(tags=["Warehouse Customers"], summary="Update a customer profile"),
)
class WarehouseScopedCustomerProfileViewSet(viewsets.ModelViewSet):
    filterset_fields = ("preferred_language", "preferred_currency", "is_suspended")
    search_fields = ("user__email", "user__full_name")
    ordering_fields = ("created_at",)
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CustomerProfileDetailSerializer
        return WarehouseCustomerProfileSerializer

    def get_queryset(self):
        return CustomerRepository.list_profiles()


@extend_schema_view(
    list=extend_schema(
        tags=["Customers"],
        summary="List wishlists",
        parameters=[
            OpenApiParameter("customer", description="Filter by customer UUID", required=False),
            OpenApiParameter("product", description="Filter by product UUID", required=False),
            OpenApiParameter("ordering", description="Order by: created_at", required=False),
        ],
    ),
    create=extend_schema(tags=["Customers"], summary="Add product to wishlist"),
    retrieve=extend_schema(tags=["Customers"], summary="Get a wishlist entry"),
    update=extend_schema(tags=["Customers"], summary="Update a wishlist entry"),
    partial_update=extend_schema(tags=["Customers"], summary="Partially update a wishlist entry"),
    destroy=extend_schema(tags=["Customers"], summary="Remove product from wishlist"),
)
class WishlistViewSet(viewsets.ModelViewSet):
    serializer_class = WishlistSerializer
    queryset = WishlistRepository.list_wishlists()
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ("customer", "product")
    ordering_fields = ("created_at",)

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_admin:
            return queryset
        return queryset.filter(customer__user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"message": "Removed from wishlist successfully."}, status=status.HTTP_200_OK)
