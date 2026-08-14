from rest_framework import serializers

from apps.coupons.models import Coupon, Offer
from core.choices import RegionChoices


class CouponSerializer(serializers.ModelSerializer):
    valid_until = serializers.DateTimeField(required=True)
    usage_limit = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = Coupon
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        from django.utils import timezone
        
        if instance.status == "inactive":
            return ret

        if instance.valid_until and instance.valid_until < timezone.now():
            ret["status"] = "expired"
            return ret

        if instance.usage_limit is not None:
            actual_usage = getattr(instance, "actual_usage", None)
            if actual_usage is None:
                from core.choices import OrderStatusChoices
                actual_usage = instance.orders.exclude(order_status=OrderStatusChoices.CANCELLED).count()
            if actual_usage >= instance.usage_limit:
                ret["status"] = "usage_exceeded"
                
        return ret

    def validate_coupon_code(self, value):
        import re
        if not re.match(r'^[A-Z0-9]+$', value):
            raise serializers.ValidationError("Coupon code must contain only capital letters and numbers.")
        return value

    def validate(self, data):
        from core.choices import CouponTypeChoices
        coupon_type = data.get("coupon_type", getattr(self.instance, "coupon_type", None))
        coupon_value = data.get("coupon_value", getattr(self.instance, "coupon_value", None))
        
        if coupon_type == CouponTypeChoices.PERCENTAGE and coupon_value > 100:
            raise serializers.ValidationError({"coupon_value": "Percentage discount cannot exceed 100%."})
            
        return data


class OfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offer
        fields = "__all__"
        read_only_fields = ("id", "warehouse", "created_at", "updated_at")


class ApplyCouponRequestSerializer(serializers.Serializer):
    coupon_code = serializers.CharField()
    region = serializers.ChoiceField(choices=RegionChoices.choices)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    warehouse_id = serializers.UUIDField(required=False, help_text="Optional warehouse UUID")

    def validate_coupon_code(self, value):
        import re
        if not re.match(r'^[A-Z0-9]+$', value):
            raise serializers.ValidationError("Coupon code must contain only capital letters and numbers.")
        return value


class ApplyCouponResponseSerializer(serializers.Serializer):
    coupon_code = serializers.CharField()
    coupon_type = serializers.CharField()
    coupon_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    original_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    discounted_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    discount_applied = serializers.DecimalField(max_digits=12, decimal_places=2)
    warehouse_id = serializers.UUIDField(required=False)
