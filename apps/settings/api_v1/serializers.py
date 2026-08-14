from rest_framework import serializers

from apps.settings.models import CurrencySettings, ShippingSettings, StoreSettings


class StoreSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreSettings
        fields = "__all__"
        read_only_fields = ("id", "warehouse", "created_at", "updated_at")


class CurrencySettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CurrencySettings
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")


class ShippingSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingSettings
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")
