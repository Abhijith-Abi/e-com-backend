from django.contrib import admin
from apps.couriers.models import Courier


@admin.register(Courier)
class CourierAdmin(admin.ModelAdmin):
    list_display = ("name", "warehouse", "courier_number", "tracking_url", "is_active", "created_at")
    search_fields = ("name", "courier_number")
    list_filter = ("warehouse",)
