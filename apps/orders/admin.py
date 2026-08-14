from django.contrib import admin

from apps.orders.models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_id", "customer", "warehouse", "courier", "tracking_number", "currency", "total_amount", "payment_status", "order_status")
    search_fields = ("order_id", "customer__user__email", "customer__user__full_name", "tracking_number")
    list_filter = ("currency", "payment_status", "order_status", "warehouse")
    autocomplete_fields = ("courier",)
    fields = (
        "order_id", "customer", "warehouse",
        "courier", "tracking_number",
        "currency", "total_amount", "gst",
        "payment_status", "order_status",
        "is_active", "created_at", "updated_at",
    )
    readonly_fields = ("order_id", "created_at", "updated_at")
    inlines = [OrderItemInline]

    def changelist_view(self, request, extra_context=None):
        from apps.orders.models import Order as O
        pending = O.objects.filter(order_status="pending", is_deleted=False).count()
        unpaid = O.objects.filter(payment_status="pending", is_deleted=False).count()
        if pending:
            self.message_user(request, f"⚠ {pending} order(s) are pending processing!", level="warning")
        if unpaid:
            self.message_user(request, f"⚠ {unpaid} order(s) have pending payment!", level="warning")
        return super().changelist_view(request, extra_context=extra_context)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "quantity", "price")
