from rest_framework import serializers

from apps.orders.models import (
    ORDER_STATUS_SEQUENCE,
    PAYMENT_STATUS_SEQUENCE,
    Order,
    OrderItem,
    OrderStatusHistory,
    PaymentStatusHistory,
)


class ShippingAddressSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    full_name = serializers.CharField()
    phone = serializers.CharField()
    address_line1 = serializers.CharField()
    address_line2 = serializers.CharField()
    city = serializers.CharField()
    state = serializers.CharField()
    postal_code = serializers.CharField()
    country = serializers.CharField()


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatusHistory
        fields = ("status", "changed_at")


class PaymentStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentStatusHistory
        fields = ("status", "changed_at")


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name_en", read_only=True)
    product_required_points = serializers.IntegerField(source="product.required_points", read_only=True)

    class Meta:
        model = OrderItem
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at", "order")


class OrderItemWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ("product", "quantity", "price", "selected_color", "selected_size")


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    items_write = OrderItemWriteSerializer(many=True, write_only=True, required=False, source="items")
    customer_name = serializers.CharField(source="customer.user.full_name", read_only=True)
    customer_email = serializers.EmailField(source="customer.user.email", read_only=True)
    courier_name = serializers.CharField(source="courier.name", read_only=True, default=None)
    courier_tracking_url = serializers.CharField(source="courier.tracking_url", read_only=True, default=None)
    shipping_address_detail = ShippingAddressSerializer(source="shipping_address", read_only=True, allow_null=True)
    applied_coupon_code = serializers.CharField(source="applied_coupon.coupon_code", read_only=True, default=None)
    status_timeline = serializers.SerializerMethodField()
    payment_timeline = serializers.SerializerMethodField()
    total_required_points = serializers.SerializerMethodField()
    applied_gift_card_name = serializers.SerializerMethodField()
    applied_gift_card_detail = serializers.SerializerMethodField()
    redeem_settings = serializers.SerializerMethodField()
    token_shortfall_charge = serializers.SerializerMethodField()

    def get_applied_gift_card_name(self, order):
        if order.applied_gift_card:
            return order.applied_gift_card.card_name
        return None

    def get_applied_gift_card_detail(self, order):
        if order.applied_gift_card:
            return {
                "id": str(order.applied_gift_card.id),
                "card_name": order.applied_gift_card.card_name,
                "discount": order.gift_card_discount,
            }
        return None
    applied_gift_wrap_detail = serializers.SerializerMethodField()
    cancellation_detail = serializers.SerializerMethodField()

    def get_redeem_settings(self, order):
        """Return active redeem settings for frontend calculations"""
        from apps.redeem.repositories import RedeemSettingsRepository
        from apps.redeem.api_v1.serializers import RedeemSettingsSerializer
        
        settings = RedeemSettingsRepository.get_active()
        if settings:
            return RedeemSettingsSerializer(settings).data
        return None

    def get_applied_gift_wrap_detail(self, order):
        if order.applied_gift_wrap:
            return {
                "id": str(order.applied_gift_wrap.id),
                "wrap_name": order.applied_gift_wrap.wrap_name,
                "charges": order.gift_wrap_charges,
            }
        return None

    class Meta:
        model = Order
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at", "order_id")

    def get_status_timeline(self, order):
        history = {h.status: h.changed_at for h in order.status_history.all()}
        timeline = []
        for s in ORDER_STATUS_SEQUENCE:
            entry = {"status": s, "reached_at": history.get(s)}
            if s == "confirmed":
                entry["ordered_at"] = order.created_at.strftime("%d %b %Y, %I:%M %p") if order.created_at else None
            timeline.append(entry)
        return timeline

    def get_payment_timeline(self, order):
        history = {h.status: h.changed_at for h in order.payment_history.all()}
        return [
            {"status": s, "reached_at": history.get(s)}
            for s in PAYMENT_STATUS_SEQUENCE
        ]

    def get_total_required_points(self, order):
        """Calculate total points required for all items in order"""
        total_points = 0
        for item in order.items.select_related('product').all():
            total_points += (item.product.required_points * item.quantity)
        return total_points

    def get_token_shortfall_charge(self, order):
        """Calculate the extra cash amount added because the user did not have enough tokens"""
        total_required = self.get_total_required_points(order)
        redeemed = order.points_redeemed or 0
        shortfall = max(0, total_required - redeemed)
        from decimal import Decimal
        return Decimal(str(shortfall)).quantize(Decimal("0.01"))

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        order = Order.objects.create(**validated_data)
        for item in items_data:
            OrderItem.objects.create(order=order, **item)
        return order

    def update(self, instance, validated_data):
        validated_data.pop("items", None)
        
        new_status = validated_data.get("order_status")
        if new_status == "cancelled" and instance.order_status != "cancelled":
            # 1. Restore product stock
            from apps.products.services import ProductService
            for item in instance.items.select_related("product").all():
                ProductService.increment_stock(
                    item.product,
                    item.quantity,
                    selected_color=item.selected_color,
                    selected_size=item.selected_size
                )

            # 2. Restore gift card stock
            if instance.applied_gift_card:
                instance.applied_gift_card.units += 1
                instance.applied_gift_card.save(update_fields=["units", "updated_at"])

            # 3. Restore gift wrap stock
            if instance.applied_gift_wrap:
                instance.applied_gift_wrap.units += 1
                instance.applied_gift_wrap.save(update_fields=["units", "updated_at"])

            # 4. Refund loyalty points
            if instance.points_redeemed and instance.points_redeemed > 0:
                from apps.redeem.services import PointWalletService
                PointWalletService.credit_points(
                    customer=instance.customer,
                    points=instance.points_redeemed,
                    description=f"Points refunded for cancelled order {instance.order_id}",
                    order=instance
                )

            # 5. Track cancellation actor & reason
            request = self.context.get("request")
            if request and request.user:
                if request.user.is_admin:
                    instance.cancelled_by = "admin"
                else:
                    instance.cancelled_by = "user"
            else:
                instance.cancelled_by = "admin"

            reason = validated_data.get("notes") or validated_data.get("cancellation_reason")
            if reason:
                instance.cancellation_reason = reason

        return super().update(instance, validated_data)

    def get_cancellation_detail(self, order):
        if order.order_status == "cancelled":
            actor = order.cancelled_by or "user"
            reason = order.cancellation_reason or order.notes or "No reason provided"
            if reason.startswith("Cancellation reason: "):
                reason = reason.replace("Cancellation reason: ", "", 1)
            
            return {
                "cancelled_by": actor,
                "reason": reason,
                "message": f"{actor.capitalize()} cancelled this order because of the reason: {reason}"
            }
        return None


class OrderTrackingTimelineSerializer(serializers.Serializer):
    status = serializers.CharField()
    reached_at = serializers.DateTimeField(allow_null=True)


class OrderTrackingSerializer(serializers.Serializer):
    order_id = serializers.CharField()
    order_status = serializers.CharField()
    courier_name = serializers.CharField(allow_null=True)
    tracking_number = serializers.CharField(allow_null=True)
    tracking_url = serializers.CharField(allow_null=True)
    status_timeline = OrderTrackingTimelineSerializer(many=True)
    items = serializers.SerializerMethodField()
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    def get_items(self, obj):
        """Return order items with product names and prices"""
        items_data = []
        # obj['items'] will be the Order instance passed from view
        order = obj.get('items') if isinstance(obj, dict) else obj
        if order and hasattr(order, 'items'):
            for item in order.items.select_related('product').all():
                items_data.append({
                    'product_name': item.product.name_en,
                    'quantity': item.quantity,
                    'price': str(item.price),
                    'selected_color': item.selected_color or None,
                    'selected_size': item.selected_size or None,
                })
        return items_data