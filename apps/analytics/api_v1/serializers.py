from rest_framework import serializers

from apps.analytics.models import StoreAnalytics


class StoreAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreAnalytics
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")


class MonthlyRevenueChartSerializer(serializers.Serializer):
    month = serializers.CharField()
    INR = serializers.FloatField(required=False)
    USD = serializers.FloatField(required=False)
    GBP = serializers.FloatField(required=False)


class SalesReportResponseSerializer(serializers.Serializer):
    date_from = serializers.DateField()
    date_to = serializers.DateField()
    currency_filter = serializers.CharField(allow_null=True)
    warehouse_id = serializers.UUIDField(allow_null=True)
    total_revenue = serializers.DictField(child=serializers.FloatField())
    total_paid_orders = serializers.IntegerField()
    cancelled_orders = serializers.IntegerField()
    cancellation_rate_pct = serializers.FloatField()
    monthly_revenue_chart = MonthlyRevenueChartSerializer(many=True)


class OrderCountByStatusSerializer(serializers.Serializer):
    status = serializers.CharField()
    count = serializers.IntegerField()


class DailyOrdersChartSerializer(serializers.Serializer):
    date = serializers.CharField()
    count = serializers.IntegerField()


class OrdersReportResponseSerializer(serializers.Serializer):
    date_from = serializers.DateField()
    date_to = serializers.DateField()
    currency_filter = serializers.CharField(allow_null=True)
    warehouse_id = serializers.UUIDField(allow_null=True)
    total_orders = serializers.IntegerField()
    by_status = OrderCountByStatusSerializer(many=True)
    daily_orders_chart = DailyOrdersChartSerializer(many=True, required=False)


class CancellationChartSerializer(serializers.Serializer):
    month = serializers.CharField()
    cancelled = serializers.IntegerField()
    refunded = serializers.IntegerField()


class CancellationReportResponseSerializer(serializers.Serializer):
    date_from = serializers.DateField()
    date_to = serializers.DateField()
    currency_filter = serializers.CharField(allow_null=True)
    warehouse_id = serializers.UUIDField(allow_null=True)
    total_cancelled = serializers.IntegerField()
    total_refunded = serializers.IntegerField()
    monthly_cancellation_chart = CancellationChartSerializer(many=True)


class ShipmentChartSerializer(serializers.Serializer):
    month = serializers.CharField()
    shipped = serializers.IntegerField()
    delivered = serializers.IntegerField()


class ShipmentReportResponseSerializer(serializers.Serializer):
    date_from = serializers.DateField()
    date_to = serializers.DateField()
    currency_filter = serializers.CharField(allow_null=True)
    warehouse_id = serializers.UUIDField(allow_null=True)
    total_shipped = serializers.IntegerField()
    total_delivered = serializers.IntegerField()
    in_transit = serializers.IntegerField()
    monthly_shipment_chart = ShipmentChartSerializer(many=True)
