from django.contrib import admin

from apps.warehouses.models import Warehouse


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ("warehouse_name", "warehouse_location", "is_active", "created_at", "flag_image")
    search_fields = ("warehouse_name", "warehouse_address")
    list_filter = ("warehouse_location", "is_active")
    fields = (
        "warehouse_name", "warehouse_address", "warehouse_location",
        "flag_image", "warehouse_details", "delivery_to", "is_active",
    )
