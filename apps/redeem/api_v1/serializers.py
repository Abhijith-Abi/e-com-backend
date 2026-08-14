from decimal import Decimal
from rest_framework import serializers

from apps.redeem.models import BillUpload, PointTransaction, PointWallet, RedeemSettings


# ─────────────────────────────────────────────────────────────────────────────
# Wallet
# ─────────────────────────────────────────────────────────────────────────────

class PointWalletSerializer(serializers.ModelSerializer):
    customer_email = serializers.CharField(source="customer.user.email", read_only=True)
    customer_name = serializers.CharField(source="customer.user.full_name", read_only=True)

    class Meta:
        model = PointWallet
        fields = (
            "id",
            "customer",
            "customer_email",
            "customer_name",
            "balance",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "balance", "created_at", "updated_at")


# ─────────────────────────────────────────────────────────────────────────────
# Bill Upload
# ─────────────────────────────────────────────────────────────────────────────

class BillUploadCreateSerializer(serializers.ModelSerializer):
    """Used by customers to submit a bill."""

    class Meta:
        model = BillUpload
        fields = ("id", "bill_image", "bill_number", "bill_price", "notes")
        read_only_fields = ("id",)


class BillUploadSerializer(serializers.ModelSerializer):
    """Full read serializer (admin + customer)."""

    customer_email = serializers.CharField(source="customer.user.email", read_only=True)
    customer_name = serializers.CharField(source="customer.user.full_name", read_only=True)
    reviewed_by_email = serializers.CharField(
        source="reviewed_by.email", read_only=True, default=None
    )

    class Meta:
        model = BillUpload
        fields = (
            "id",
            "customer",
            "customer_email",
            "customer_name",
            "bill_image",
            "bill_number",
            "bill_price",
            "bill_code",        # ← add this line
            "notes",
            "status",
            "admin_notes",
            "points_awarded",
            "reviewed_by",
            "reviewed_by_email",
            "reviewed_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class AdminApproveBillSerializer(serializers.Serializer):
    """Payload for admin to approve a bill and award points."""

    bill_price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"), help_text="Verified bill price")
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class AdminRejectBillSerializer(serializers.Serializer):
    """Payload for admin to reject a bill."""

    notes = serializers.CharField(required=False, allow_blank=True, default="")


# ─────────────────────────────────────────────────────────────────────────────
# Point Transaction
# ─────────────────────────────────────────────────────────────────────────────

class PointTransactionSerializer(serializers.ModelSerializer):
    customer_email = serializers.CharField(
        source="wallet.customer.user.email", read_only=True
    )
    bill_code = serializers.SerializerMethodField()
    product_name = serializers.SerializerMethodField()

    class Meta:
        model = PointTransaction
        fields = (
            "id",
            "wallet",
            "customer_email",
            "transaction_type",
            "points",
            "balance_after",
            "description",
            "bill_upload",
            "bill_code",
            "order",
            "product_name",
            "created_at",
        )
        read_only_fields = (
            "id",
            "wallet",
            "customer_email",
            "transaction_type",
            "points",
            "balance_after",
            "description",
            "bill_upload",
            "bill_code",
            "order",
            "product_name",
            "created_at",
        )

    def get_bill_code(self, obj):
        """Fetch bill_code from related BillUpload if it exists."""
        if obj.bill_upload:
            return obj.bill_upload.bill_code
        return None

    def get_product_name(self, obj):
        """Fetch comma-separated product names if linked to an order."""
        if obj.order:
            # We assume order__items__product is prefetched
            return ", ".join(
                [item.product.name_en for item in obj.order.items.all() if item.product and item.product.name_en]
            )
        return None

# ─────────────────────────────────────────────────────────────────────────────
# Redeem Settings
# ─────────────────────────────────────────────────────────────────────────────

class RedeemSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RedeemSettings
        fields = (
            "id",
            "points_per_currency_unit",
            "min_points_to_redeem",
            "max_redeem_percent",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


# ─────────────────────────────────────────────────────────────────────────────
# Checkout – Preview
# ─────────────────────────────────────────────────────────────────────────────

class RedeemPointsCheckSerializer(serializers.Serializer):
    """
    Dry-run: how much discount does N points give on a given order total?
    """

    points_to_redeem = serializers.IntegerField(
        min_value=1,
        help_text="Number of points the customer wants to redeem",
    )
    order_total = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Current order subtotal (after coupon, before points)",
    )


class RedeemPointsCheckResponseSerializer(serializers.Serializer):
    points_to_redeem = serializers.IntegerField()
    discount_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    order_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    final_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    wallet_balance = serializers.IntegerField()
    is_valid = serializers.BooleanField()
    error = serializers.CharField(allow_null=True)


# ─────────────────────────────────────────────────────────────────────────────
# Checkout – Apply to existing order
# ─────────────────────────────────────────────────────────────────────────────

class RedeemAtCheckoutSerializer(serializers.Serializer):
    """
    Apply points to an already-created order.
    Also used as the `points_to_redeem` field in the cart checkout payload.
    """

    points_to_redeem = serializers.IntegerField(
        min_value=1,
        help_text="Number of points to redeem against this order",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Product Redeem (points-only purchase)
# ─────────────────────────────────────────────────────────────────────────────

class _NewAddressSerializer(serializers.Serializer):
    full_name = serializers.CharField()
    phone = serializers.CharField()
    address_line1 = serializers.CharField()
    address_line2 = serializers.CharField(required=False, allow_blank=True, default="")
    city = serializers.CharField()
    state = serializers.CharField()
    postal_code = serializers.CharField()
    country = serializers.CharField()


class ProductRedeemSerializer(serializers.Serializer):
    """
    Request body for redeeming a product entirely with loyalty points.
    The product must have `redeem_points` set (not null).
    """

    product = serializers.UUIDField(help_text="UUID of the product to redeem")
    warehouse = serializers.UUIDField(help_text="UUID of the warehouse")
    quantity = serializers.IntegerField(
        min_value=1,
        default=1,
        help_text="Quantity to redeem (default: 1)",
    )
    address_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text="UUID of an existing saved CustomerAddress (optional)",
    )
    new_address = _NewAddressSerializer(
        required=False,
        allow_null=True,
        help_text="Provide a new address inline instead of address_id (optional)",
    )


class ProductRedeemResponseSerializer(serializers.Serializer):
    order_id = serializers.CharField()
    order_uuid = serializers.UUIDField()
    product = serializers.UUIDField()
    product_name = serializers.CharField()
    quantity = serializers.IntegerField()
    points_used = serializers.IntegerField()
    wallet_balance_after = serializers.IntegerField()
