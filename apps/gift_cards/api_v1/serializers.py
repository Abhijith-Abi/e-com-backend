from rest_framework import serializers

from apps.gift_cards.models import (
    GiftCard,
    GiftCardCategory,
    GiftCardWrap,
    LowStockGiftCardNotification,
    LowStockGiftCardWrapNotification,
)


class GiftCardCategorySerializer(serializers.ModelSerializer):
    cards = serializers.SerializerMethodField()

    class Meta:
        model = GiftCardCategory
        fields = "__all__"
        read_only_fields = ("id", "warehouse", "created_at", "updated_at")

    def get_cards(self, obj):
        return obj.gift_cards.filter(is_deleted=False).count()

    def validate_name(self, value):
        request = self.context.get("request")
        warehouse = getattr(request, "warehouse", None)
        if warehouse:
            qs = GiftCardCategory.objects.filter(warehouse=warehouse, name__iexact=value)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    "A gift card category with the name '{}' already exists in this warehouse.".format(value)
                )
        return value


class GiftCardWrapSerializer(serializers.ModelSerializer):
    delete_image = serializers.BooleanField(write_only=True, required=False, default=False)

    class Meta:
        model = GiftCardWrap
        fields = "__all__"
        read_only_fields = ("id", "warehouse", "created_at", "updated_at")

    def create(self, validated_data):
        validated_data.pop("delete_image", None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        delete_image = validated_data.pop("delete_image", False)
        if delete_image:
            if instance.image:
                instance.image.delete(save=False)
            validated_data["image"] = None
        elif "image" not in validated_data:
            validated_data["image"] = instance.image
        return super().update(instance, validated_data)

    def validate_wrap_name(self, value):
        request = self.context.get("request")
        warehouse = getattr(request, "warehouse", None)
        if warehouse:
            qs = GiftCardWrap.objects.filter(warehouse=warehouse, wrap_name__iexact=value)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    "A gift card wrap with the name '{}' already exists in this warehouse.".format(value)
                )
        return value


class GiftCardSerializer(serializers.ModelSerializer):
    delete_image = serializers.BooleanField(write_only=True, required=False, default=False)
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = GiftCard
        fields = "__all__"
        read_only_fields = ("id", "warehouse", "created_at", "updated_at")

    def create(self, validated_data):
        validated_data.pop("delete_image", None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        delete_image = validated_data.pop("delete_image", False)
        if delete_image:
            if instance.image:
                instance.image.delete(save=False)
            validated_data["image"] = None
        elif "image" not in validated_data:
            validated_data["image"] = instance.image
        return super().update(instance, validated_data)

    def validate_card_name(self, value):
        request = self.context.get("request")
        warehouse = getattr(request, "warehouse", None)
        if warehouse:
            qs = GiftCard.objects.filter(warehouse=warehouse, card_name__iexact=value)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    "A gift card with the name '{}' already exists in this warehouse.".format(value)
                )
        return value


class LowStockGiftCardNotificationSerializer(serializers.ModelSerializer):
    gift_card_name = serializers.CharField(source="gift_card.card_name", read_only=True)

    class Meta:
        model = LowStockGiftCardNotification
        fields = ["id", "gift_card", "gift_card_name", "remaining_units", "threshold", "message", "is_read", "notified_at"]


class LowStockGiftCardWrapNotificationSerializer(serializers.ModelSerializer):
    wrap_name = serializers.CharField(source="gift_card_wrap.wrap_name", read_only=True)

    class Meta:
        model = LowStockGiftCardWrapNotification
        fields = ["id", "gift_card_wrap", "wrap_name", "remaining_units", "threshold", "message", "is_read", "notified_at"]
