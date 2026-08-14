from django.contrib import admin

from apps.payments.models import Payment, PaymentMethod


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "code")
    list_editable = ("is_active",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("order", "payment_method", "payment_status", "transaction_id")
    search_fields = ("transaction_id", "order__order_id")
    list_filter = ("payment_method", "payment_status")
