from apps.analytics.models import StoreAnalytics


class AnalyticsRepository:
    @staticmethod
    def list_analytics():
        return StoreAnalytics.objects.order_by("-created_at")
