from decimal import Decimal

from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view, inline_serializer
from rest_framework import fields as drf_fields
from rest_framework import permissions, status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.customers.services import CustomerService
from apps.redeem.api_v1.serializers import (
    AdminApproveBillSerializer,
    AdminRejectBillSerializer,
    BillUploadCreateSerializer,
    BillUploadSerializer,
    PointTransactionSerializer,
    PointWalletSerializer,
    ProductRedeemSerializer,
    ProductRedeemResponseSerializer,
    RedeemAtCheckoutSerializer,
    RedeemPointsCheckResponseSerializer,
    RedeemPointsCheckSerializer,
    RedeemSettingsSerializer,
)
from apps.redeem.models import BillStatusChoices, PointWallet
from apps.redeem.repositories import (
    BillUploadRepository,
    PointTransactionRepository,
    PointWalletRepository,
    RedeemSettingsRepository,
)
from apps.redeem.services import BillUploadService, PointWalletService
from core.permissions import IsAdminOrReadOnly


# ─────────────────────────────────────────────────────────────────────────────
# Wallet
# ─────────────────────────────────────────────────────────────────────────────

@extend_schema(tags=["Redeem – Wallet"])
class MyWalletView(APIView):
    """Return the authenticated customer's point wallet (creates one if missing)."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get my point wallet",
        description="Returns the current customer's wallet balance and metadata.",
        responses={200: PointWalletSerializer},
    )
    def get(self, request):
        customer = CustomerService.ensure_profile(request.user)
        wallet = PointWalletRepository.get_or_create_for_customer(customer)
        return Response(PointWalletSerializer(wallet).data)


@extend_schema_view(
    list=extend_schema(
        tags=["Redeem – Admin"],
        summary="List all customer wallets",
        parameters=[
            OpenApiParameter("customer", description="Filter by customer UUID", required=False),
            OpenApiParameter("search", description="Search by name or email", required=False),
        ],
    ),
    retrieve=extend_schema(tags=["Redeem – Admin"], summary="Get a specific wallet"),
)
class PointWalletViewSet(viewsets.ReadOnlyModelViewSet):
    """Admin-only: browse all customer wallets."""

    serializer_class = PointWalletSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ("customer",)
    search_fields = ("customer__user__email", "customer__user__full_name")

    def get_queryset(self):
        return PointWallet.objects.select_related("customer__user").order_by("-balance")


# ─────────────────────────────────────────────────────────────────────────────
# Bill Upload
# ─────────────────────────────────────────────────────────────────────────────

@extend_schema(tags=["Redeem – Bills"])
class MyBillUploadView(APIView):
    """Customer: list own bills and submit a new one."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="List my bill uploads",
        description="Returns all bills the authenticated customer has submitted.",
        responses={200: BillUploadSerializer(many=True)},
    )
    def get(self, request):
        customer = CustomerService.ensure_profile(request.user)
        bills = BillUploadRepository.list_for_customer(customer)
        return Response(BillUploadSerializer(bills, many=True, context={"request": request}).data)

    @extend_schema(
        summary="Upload a new bill",
        description=(
            "Customer uploads a purchase bill image. "
            "Admin will review it and manually award points."
        ),
        request=BillUploadCreateSerializer,
        responses={201: BillUploadSerializer},
    )
    def post(self, request):
        customer = CustomerService.ensure_profile(request.user)
        serializer = BillUploadCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        bill = serializer.save(customer=customer)
        return Response(
            BillUploadSerializer(bill, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    list=extend_schema(
        tags=["Redeem – Admin"],
        summary="List all bill uploads",
        parameters=[
            OpenApiParameter(
                "status",
                description="Filter by status: pending | approved | rejected",
                required=False,
            ),
            OpenApiParameter("customer", description="Filter by customer UUID", required=False),
            OpenApiParameter(
                "search",
                description="Search by bill_number or customer email",
                required=False,
            ),
        ],
    ),
    retrieve=extend_schema(tags=["Redeem – Admin"], summary="Get a bill upload detail"),
)
class AdminBillUploadViewSet(viewsets.ReadOnlyModelViewSet):
    """Admin-only: view and action on all bill uploads."""

    serializer_class = BillUploadSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ("status", "customer")
    search_fields = ("bill_code", "customer__user__email", "customer__user__full_name")

    def get_queryset(self):
        return BillUploadRepository.list_all()

    @extend_schema(
        tags=["Redeem – Admin"],
        summary="Approve a bill and award points",
        description=(
            "Admin reviews the uploaded bill, enters the number of points to award, "
            "and optionally adds a note. Points are immediately credited to the customer's wallet."
        ),
        request=AdminApproveBillSerializer,
        responses={200: BillUploadSerializer},
    )
    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        bill = self.get_object()
        serializer = AdminApproveBillSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            bill = BillUploadService.approve_bill(
                bill=bill,
                admin_user=request.user,
                bill_price=serializer.validated_data["bill_price"],
                admin_notes=serializer.validated_data.get("notes", ""),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(BillUploadSerializer(bill, context={"request": request}).data)

    @extend_schema(
        tags=["Redeem – Admin"],
        summary="Reject a bill",
        description="Admin rejects the bill. No points are awarded. An optional note can be added.",
        request=AdminRejectBillSerializer,
        responses={200: BillUploadSerializer},
    )
    @action(detail=True, methods=["post"], url_path="reject")
    def reject(self, request, pk=None):
        bill = self.get_object()
        serializer = AdminRejectBillSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            bill = BillUploadService.reject_bill(
                bill=bill,
                admin_user=request.user,
                admin_notes=serializer.validated_data.get("notes", ""),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(BillUploadSerializer(bill, context={"request": request}).data)


# ─────────────────────────────────────────────────────────────────────────────
# Transactions
# ─────────────────────────────────────────────────────────────────────────────

from rest_framework import generics
from rest_framework.pagination import PageNumberPagination

class TransactionPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

@extend_schema(tags=["Redeem – Wallet"])
class MyTransactionListView(generics.ListAPIView):
    """Customer: view own point transaction history."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PointTransactionSerializer
    pagination_class = TransactionPagination

    @extend_schema(
        summary="List my point transactions",
        description="Returns all credit and debit transactions for the authenticated customer's wallet.",
        responses={200: PointTransactionSerializer(many=True)},
    )
    def get_queryset(self):
        customer = CustomerService.ensure_profile(self.request.user)
        wallet = PointWalletRepository.get_or_create_for_customer(customer)
        return PointTransactionRepository.list_for_wallet(wallet)


@extend_schema_view(
    list=extend_schema(
        tags=["Redeem – Admin"],
        summary="List all point transactions",
        parameters=[
            OpenApiParameter("wallet", description="Filter by wallet UUID", required=False),
            OpenApiParameter(
                "transaction_type",
                description="Filter by type: credit | debit",
                required=False,
            ),
        ],
    ),
    retrieve=extend_schema(tags=["Redeem – Admin"], summary="Get a point transaction"),
)
class AdminPointTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """Admin-only: view all point transactions across all customers."""

    serializer_class = PointTransactionSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ("wallet", "transaction_type")

    def get_queryset(self):
        return PointTransactionRepository.list_all()


# ─────────────────────────────────────────────────────────────────────────────
# Redeem Settings
# ─────────────────────────────────────────────────────────────────────────────

@extend_schema_view(
    list=extend_schema(
        tags=["Redeem – Settings"],
        summary="List redeem settings",
        description="Returns all redeem configuration rows. The active one (is_active=true) is used system-wide.",
    ),
    create=extend_schema(
        tags=["Redeem – Settings"],
        summary="Create redeem settings",
        description="Admin creates a new settings row. Set is_active=true to make it the active config.",
    ),
    retrieve=extend_schema(tags=["Redeem – Settings"], summary="Get a redeem settings row"),
    update=extend_schema(tags=["Redeem – Settings"], summary="Update redeem settings"),
    partial_update=extend_schema(tags=["Redeem – Settings"], summary="Partially update redeem settings"),
    destroy=extend_schema(tags=["Redeem – Settings"], summary="Delete a redeem settings row"),
)
class RedeemSettingsViewSet(viewsets.ModelViewSet):
    """Admin manages the global points configuration."""

    serializer_class = RedeemSettingsSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        from apps.redeem.models import RedeemSettings
        return RedeemSettings.objects.order_by("-created_at")
    
        
    def create(self, request, *args, **kwargs):
        return Response(
            {"detail": "Creating new settings is not allowed. Please update the existing settings."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
        
    def destroy(self, request, *args, **kwargs):
        return Response(
            {"detail": "Deleting settings is not allowed."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )




# ─────────────────────────────────────────────────────────────────────────────
# Checkout – Preview
# ─────────────────────────────────────────────────────────────────────────────

@extend_schema(tags=["Redeem – Checkout"])
class RedeemPointsCheckView(APIView):
    """
    Preview how much discount a customer gets for a given number of points
    before placing the order. Does NOT deduct any points.
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Preview points redemption discount",
        description=(
            "Pass `points_to_redeem` and `order_total` to get back the discount amount "
            "and final total. No points are deducted — this is a dry-run check.\n\n"
            "Use this before calling checkout to show the customer what they'll save."
        ),
        request=RedeemPointsCheckSerializer,
        responses={200: RedeemPointsCheckResponseSerializer},
    )
    def post(self, request):
        serializer = RedeemPointsCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        customer = CustomerService.ensure_profile(request.user)
        points_to_redeem = serializer.validated_data["points_to_redeem"]
        order_total = Decimal(str(serializer.validated_data["order_total"]))
        redeem_settings = RedeemSettingsRepository.get_active()
        wallet = PointWalletRepository.get_or_create_for_customer(customer)

        is_valid, error, discount = PointWalletService.validate_redemption(
            customer, points_to_redeem, order_total, redeem_settings
        )

        response_data = {
            "points_to_redeem": points_to_redeem,
            "discount_amount": discount,
            "order_total": order_total,
            "final_total": max(order_total - discount, Decimal("0.00")),
            "wallet_balance": wallet.balance,
            "is_valid": is_valid,
            "error": error,
        }
        return Response(RedeemPointsCheckResponseSerializer(response_data).data)


# ─────────────────────────────────────────────────────────────────────────────
# Checkout – Apply to existing order
# ─────────────────────────────────────────────────────────────────────────────

@extend_schema(tags=["Redeem – Checkout"])
class RedeemPointsApplyView(APIView):
    """
    Apply points redemption to an already-created order.
    Use this if you want to let the customer apply points after order creation
    (e.g. on a payment confirmation screen).

    Alternatively, pass `points_to_redeem` directly in the cart checkout payload
    to handle everything in one step.
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Apply points to an existing order",
        description=(
            "Deducts `points_to_redeem` from the customer's wallet and reduces "
            "`order.total_amount` by the equivalent currency value.\n\n"
            "Can only be applied once per order (before payment is completed)."
        ),
        request=RedeemAtCheckoutSerializer,
        responses={
            200: RedeemPointsCheckResponseSerializer,
            400: inline_serializer(
                name="RedeemApplyError",
                fields={"detail": drf_fields.CharField()},
            ),
            404: inline_serializer(
                name="RedeemApplyNotFound",
                fields={"detail": drf_fields.CharField()},
            ),
        },
    )
    def post(self, request, order_id):
        from django.db import transaction as db_transaction

        from apps.orders.models import Order

        customer = CustomerService.ensure_profile(request.user)
        serializer = RedeemAtCheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        points_to_redeem = serializer.validated_data.get("points_to_redeem", 0)
        if points_to_redeem == 0:
            return Response(
                {"detail": "points_to_redeem must be greater than 0."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            order = Order.objects.get(id=order_id, customer=customer)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        if order.points_redeemed > 0:
            return Response(
                {"detail": "Points have already been applied to this order."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        redeem_settings = RedeemSettingsRepository.get_active()
        wallet = PointWalletRepository.get_or_create_for_customer(customer)
        is_valid, error, discount, points_actually_redeemed = PointWalletService.validate_redemption(
            customer, points_to_redeem, order.total_amount, redeem_settings
        )


        if not is_valid:
            return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)

        with db_transaction.atomic():
            PointWalletService.debit_points(
                customer=customer,
                points=points_to_redeem,
                description=f"Redeemed for order {order.order_id}",
                order=order,
            )
            order.discount_amount = (order.discount_amount or Decimal("0.00")) + discount
            order.total_amount = max(order.total_amount - discount, Decimal("0.00"))
            order.points_redeemed = points_to_redeem
            order.save(update_fields=["discount_amount", "total_amount", "points_redeemed", "updated_at"])

        wallet = PointWalletRepository.get_or_create_for_customer(customer)
        response_data = {
            "points_to_redeem": points_to_redeem,
            "discount_amount": discount,
            "order_total": order.total_amount,
            "final_total": order.total_amount,
            "wallet_balance": wallet.balance,
            "is_valid": True,
            "error": None,
        }
        return Response(RedeemPointsCheckResponseSerializer(response_data).data)


# ─────────────────────────────────────────────────────────────────────────────
# Product Redeem (points-only purchase)
# ─────────────────────────────────────────────────────────────────────────────

@extend_schema(tags=["Redeem – Product"])
class ProductRedeemView(APIView):
    """
    Redeem a product using loyalty points only (no money required).
    The product must have `redeem_points` set (not null/blank).
    Points are deducted from the customer's wallet and an order is created.
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Redeem a product using points",
        description=(
            "If a product has `redeem_points` set, the customer can 'purchase' it "
            "entirely with loyalty points. No payment is required.\n\n"
            "**Flow:**\n"
            "1. Check product has `redeem_points` set\n"
            "2. Validate customer has enough points\n"
            "3. Deduct points from wallet\n"
            "4. Create an order with `total_amount = 0` and `points_redeemed = N`\n\n"
            "Pass `warehouse` (required), optional `address_id` or `new_address`."
        ),
        request=ProductRedeemSerializer,
        responses={
            201: ProductRedeemResponseSerializer,
            400: inline_serializer(
                name="ProductRedeemError",
                fields={"detail": drf_fields.CharField()},
            ),
        },
    )
    def post(self, request):
        from django.db import transaction as db_transaction

        from apps.customers.models import CustomerAddress
        from apps.orders.models import Order, OrderItem
        from apps.orders.services import OrderService
        from apps.payments.models import Payment, PaymentMethod
        from apps.products.models import Product
        from apps.warehouses.models import Warehouse
        from core.choices import PaymentStatusChoices

        serializer = ProductRedeemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        customer = CustomerService.ensure_profile(request.user)
        product_id = serializer.validated_data["product"]
        warehouse_id = serializer.validated_data["warehouse"]
        quantity = serializer.validated_data.get("quantity", 1)
        address_id = serializer.validated_data.get("address_id")
        address_data = serializer.validated_data.get("new_address")

        # Validate product
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

        if product.redeem_points is None:
            return Response(
                {"detail": "This product is not available for points redemption."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        total_points_needed = product.redeem_points * quantity
        wallet = PointWalletRepository.get_or_create_for_customer(customer)

        if wallet.balance < total_points_needed:
            return Response(
                {
                    "detail": (
                        f"Insufficient points. You need {total_points_needed} points "
                        f"({product.redeem_points} × {quantity}), but have {wallet.balance}."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate warehouse
        try:
            warehouse = Warehouse.objects.get(id=warehouse_id)
        except Warehouse.DoesNotExist:
            return Response({"detail": "Warehouse not found."}, status=status.HTTP_404_NOT_FOUND)

        # Resolve shipping address
        shipping_address = None
        if address_id:
            shipping_address = CustomerAddress.objects.filter(
                id=address_id, customer=customer
            ).first()
        elif address_data:
            shipping_address = CustomerAddress.objects.create(
                customer=customer,
                full_name=address_data.get("full_name", ""),
                phone=address_data.get("phone", ""),
                address_line1=address_data.get("address_line1", ""),
                address_line2=address_data.get("address_line2", ""),
                city=address_data.get("city", ""),
                state=address_data.get("state", ""),
                postal_code=address_data.get("postal_code", ""),
                country=address_data.get("country", ""),
                is_default=False,
            )
        else:
            shipping_address = customer.addresses.filter(is_default=True).first()

        with db_transaction.atomic():
            # Create order with zero total (fully paid by points)
            order = Order.objects.create(
                order_id=OrderService.generate_order_id(),
                customer=customer,
                warehouse=warehouse,
                shipping_address=shipping_address,
                currency=customer.preferred_currency,
                total_amount=Decimal("0.00"),
                gst=Decimal("0.00"),
                discount_amount=Decimal("0.00"),
                points_redeemed=total_points_needed,
            )
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=Decimal("0.00"),
            )
            # Create a payment record (COD/free)
            pm = PaymentMethod.objects.filter(is_active=True).order_by("name").first()
            Payment.objects.create(
                order=order,
                payment_method=pm,
                payment_status=PaymentStatusChoices.PAID,  # free — no money needed
            )
            # Deduct points
            PointWalletService.debit_points(
                customer=customer,
                points=total_points_needed,
                description=f"Redeemed {quantity}× '{product.name_en}' (order {order.order_id})",
                order=order,
            )

        wallet = PointWalletRepository.get_or_create_for_customer(customer)
        return Response(
            {
                "order_id": order.order_id,
                "order_uuid": str(order.id),
                "product": str(product.id),
                "product_name": product.name_en,
                "quantity": quantity,
                "points_used": total_points_needed,
                "wallet_balance_after": wallet.balance,
            },
            status=status.HTTP_201_CREATED,
        )
