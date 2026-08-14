from django.contrib import admin

from apps.analytics.models import StoreAnalytics


@admin.register(StoreAnalytics)
class StoreAnalyticsAdmin(admin.ModelAdmin):
    list_display = ("total_revenue", "total_orders", "cancellation_rate", "created_at")
