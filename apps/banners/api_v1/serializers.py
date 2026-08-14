from rest_framework import serializers

from apps.banners.models import Banner, Testimonial


class BannerSerializer(serializers.ModelSerializer):
    delete_image = serializers.BooleanField(write_only=True, required=False, default=False)
    warehouse_name = serializers.CharField(source="warehouse.warehouse_name", read_only=True)

    class Meta:
        model = Banner
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


class TestimonialSerializer(serializers.ModelSerializer):
    warehouse_name = serializers.CharField(source="warehouse.warehouse_name", read_only=True)

    class Meta:
        model = Testimonial
        fields = "__all__"
        read_only_fields = ("id", "warehouse", "created_at", "updated_at")
