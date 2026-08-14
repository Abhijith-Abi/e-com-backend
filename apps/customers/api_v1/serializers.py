from rest_framework import serializers

from apps.customers.models import CustomerAddress, CustomerProfile, Wishlist
from apps.orders.models import Order


class CustomerAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerAddress
        fields = (
            "id",
            "customer",
            "full_name",
            "phone",
            "address_line1",
            "address_line2",
            "city",
            "state",
            "postal_code",
            "country",
            "is_default",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "customer", "created_at", "updated_at")


class CustomerOrderItemSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    product = serializers.UUIDField()
    product_name = serializers.CharField(source="product.name_en")
    quantity = serializers.IntegerField()
    price = serializers.DecimalField(max_digits=12, decimal_places=2)


class CustomerOrderSerializer(serializers.ModelSerializer):
    items = CustomerOrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "order_id",
            "currency",
            "total_amount",
            "gst",
            "payment_status",
            "order_status",
            "items",
            "created_at",
            "updated_at",
        )


class CustomerProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source="user.id", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_full_name = serializers.CharField(source="user.full_name", read_only=True)
    user_phone = serializers.CharField(source="user.phone", read_only=True)
    user_role = serializers.CharField(source="user.role", read_only=True)
    user_is_verified = serializers.BooleanField(source="user.is_verified", read_only=True)
    user_is_active = serializers.BooleanField(source="user.is_active", read_only=True)
    user_date_joined = serializers.DateTimeField(source="user.created_at", read_only=True)
    addresses = CustomerAddressSerializer(many=True, read_only=True)

    class Meta:
        model = CustomerProfile
        fields = (
            "id",
            "user",
            "user_id",
            "user_email",
            "user_full_name",
            "user_phone",
            "user_role",
            "user_is_verified",
            "user_is_active",
            "user_date_joined",
            "preferred_language",
            "preferred_currency",
            "country",
            "is_suspended",
            "is_active",
            "addresses",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class WarehouseCustomerProfileSerializer(CustomerProfileSerializer):
    warehouse = serializers.SerializerMethodField()

    class Meta(CustomerProfileSerializer.Meta):
        fields = CustomerProfileSerializer.Meta.fields + ("warehouse",)

    def get_warehouse(self, obj):
        request = self.context.get("request")
        if request and hasattr(request, "warehouse") and request.warehouse:
            return str(request.warehouse.id)
        return None


class CustomerProfileDetailSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    phone = serializers.CharField(source="user.phone", read_only=True)
    orders = CustomerOrderSerializer(many=True, read_only=True)
    addresses = CustomerAddressSerializer(many=True, read_only=True)

    class Meta:
        model = CustomerProfile
        fields = (
            "id",
            "full_name",
            "email",
            "phone",
            "preferred_language",
            "preferred_currency",
            "is_suspended",
            "is_active",
            "orders",
            "addresses",
            "created_at",
            "updated_at",
        )


class WishlistSerializer(serializers.ModelSerializer):
    product_detail = serializers.SerializerMethodField()

    class Meta:
        model = Wishlist
        fields = ("id", "customer", "product", "product_detail", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at", "product_detail")

    def get_product_detail(self, obj):
        from apps.cart.api_v1.serializers import CartItemProductSerializer
        return CartItemProductSerializer(obj.product, context=self.context).data
