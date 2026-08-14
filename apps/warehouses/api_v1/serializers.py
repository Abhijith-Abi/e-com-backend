from rest_framework import serializers

from apps.warehouses.models import Warehouse


class WarehouseSerializer(serializers.ModelSerializer):
    delete_flag_image = serializers.BooleanField(write_only=True, required=False, default=False)

    class Meta:
        model = Warehouse
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")

    def create(self, validated_data):
        validated_data.pop("delete_flag_image", None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        delete_flag_image = validated_data.pop("delete_flag_image", False)
        if delete_flag_image:
            if instance.flag_image:
                instance.flag_image.delete(save=False)
            validated_data["flag_image"] = None
        elif "flag_image" not in validated_data:
            validated_data["flag_image"] = instance.flag_image
        return super().update(instance, validated_data)
