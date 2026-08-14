from rest_framework import serializers
from apps.couriers.models import Courier


class CourierSerializer(serializers.ModelSerializer):
    warehouse_name = serializers.CharField(source="warehouse.warehouse_name", read_only=True)

    class Meta:
        model = Courier
        fields = "__all__"
        read_only_fields = ("id", "warehouse", "created_at", "updated_at")
