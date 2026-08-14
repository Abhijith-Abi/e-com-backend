from django.db.models import Count, Q, Sum

from apps.analytics.models import StoreAnalytics
from apps.orders.models import Order
from core.choices import OrderStatusChoices


class AnalyticsService:
    @staticmethod
    def snapshot():
        aggregates = Order.objects.aggregate(total_revenue=Sum("total_amount"), total_orders=Count("id"))
        cancelled = Order.objects.filter(order_status=OrderStatusChoices.CANCELLED).count()
        total_orders = aggregates["total_orders"] or 0
        cancellation_rate = (cancelled / total_orders * 100) if total_orders else 0
        return StoreAnalytics.objects.create(
            total_revenue=aggregates["total_revenue"] or 0,
            total_orders=total_orders,
            cancellation_rate=cancellation_rate,
        )
