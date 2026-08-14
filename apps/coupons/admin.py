from django.contrib import admin

from apps.coupons.models import Coupon, CouponUsage, Offer


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("coupon_code", "coupon_type", "coupon_value", "region", "status", "valid_until", "usage_count")
    search_fields = ("coupon_code",)
    list_filter = ("coupon_type", "region", "status")

    def usage_count(self, obj):
        """Display how many times this coupon has been used"""
        return obj.usage_records.count()
    usage_count.short_description = "Times Used"

    def changelist_view(self, request, extra_context=None):
        from django.utils import timezone
        from datetime import timedelta
        now = timezone.now()
        expiring_soon = Coupon.objects.filter(
            status="active",
            valid_until__date__gte=now.date(),
            valid_until__date__lte=(now + timedelta(days=3)).date(),
        ).count()
        expired = Coupon.objects.filter(
            status="active",
            valid_until__date__lt=now.date(),
        ).count()
        if expired:
            self.message_user(request, f"⚠ {expired} coupon(s) have expired but are still active!", level="error")
        if expiring_soon:
            self.message_user(request, f"⚠ {expiring_soon} coupon(s) are expiring within 3 days!", level="warning")
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ("coupon", "customer", "order", "used_at")
    search_fields = ("coupon__coupon_code", "customer__user__email", "order__order_id")
    list_filter = ("used_at", "coupon")
    readonly_fields = ("coupon", "customer", "order", "used_at")
    
    def has_add_permission(self, request):
        # Prevent manual creation - should only be created automatically
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Allow deletion for admin corrections
        return True


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ("heading_en", "warehouse", "status", "created_at")
    search_fields = ("heading_en", "heading_ar")
    list_filter = ("status", "warehouse")
