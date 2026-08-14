from django.contrib import admin

from apps.redeem.models import BillUpload, PointTransaction, PointWallet, RedeemSettings


@admin.register(PointWallet)
class PointWalletAdmin(admin.ModelAdmin):
    list_display = ("customer_name", "customer_email", "balance", "updated_at")
    search_fields = ("customer__user__email", "customer__user__full_name")
    readonly_fields = ("balance", "created_at", "updated_at")
    ordering = ("-updated_at",)

    def customer_name(self, obj):
        return obj.customer.user.full_name
    customer_name.short_description = "Name"

    def customer_email(self, obj):
        return obj.customer.user.email
    customer_email.short_description = "Email"


@admin.register(BillUpload)
class BillUploadAdmin(admin.ModelAdmin):
    list_display = ("bill_number", "customer_name", "customer_email", "bill_price", "status", "points_awarded", "reviewed_by", "created_at")
    list_filter = ("status",)
    search_fields = ("bill_number", "customer__user__email", "customer__user__full_name")
    readonly_fields = ("reviewed_at", "created_at", "updated_at")
    ordering = ("-created_at",)
    list_per_page = 10

    def changelist_view(self, request, extra_context=None):
        pending = BillUpload.objects.filter(status="pending", is_deleted=False).count()
        if pending:
            self.message_user(request, f"⚠ {pending} bill upload(s) are pending review!", level="warning")
        return super().changelist_view(request, extra_context=extra_context)

    def customer_name(self, obj):
        return obj.customer.user.full_name
    customer_name.short_description = "Name"

    def customer_email(self, obj):
        return obj.customer.user.email
    customer_email.short_description = "Email"


@admin.register(PointTransaction)
class PointTransactionAdmin(admin.ModelAdmin):
    list_display = ("customer_name", "customer_email", "transaction_type", "points", "balance_after", "description", "order", "created_at")
    list_filter = ("transaction_type",)
    search_fields = ("wallet__customer__user__email", "wallet__customer__user__full_name")
    readonly_fields = ("wallet", "transaction_type", "points", "balance_after", "bill_upload", "order", "created_at", "updated_at")
    ordering = ("-created_at",)
    list_per_page = 10

    def customer_name(self, obj):
        return obj.wallet.customer.user.full_name
    customer_name.short_description = "Name"

    def customer_email(self, obj):
        return obj.wallet.customer.user.email
    customer_email.short_description = "Email"


@admin.register(RedeemSettings)
class RedeemSettingsAdmin(admin.ModelAdmin):
    list_display = ("points_per_currency_unit", "min_points_to_redeem", "max_redeem_percent", "is_active", "updated_at")
