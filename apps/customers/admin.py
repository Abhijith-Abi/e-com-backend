from django.contrib import admin
from django.contrib import messages

from apps.customers.models import CustomerProfile, Wishlist


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "preferred_language", "preferred_currency", "is_suspended")
    search_fields = ("user__email", "user__full_name")
    list_filter = ("preferred_language", "preferred_currency", "is_suspended")
    actions = ["suspend_customers", "unsuspend_customers", "delete_customers"]

    def changelist_view(self, request, extra_context=None):
        suspended = CustomerProfile.objects.filter(is_suspended=True, is_deleted=False).count()
        if suspended:
            self.message_user(request, f"⚠ {suspended} customer(s) are currently suspended!", level="warning")
        return super().changelist_view(request, extra_context=extra_context)

    def suspend_customers(self, request, queryset):
        updated = queryset.update(is_suspended=True)
        queryset.values_list("user", flat=True)
        from apps.user_account.models import User
        User.objects.filter(customer_profile__in=queryset).update(is_active=False)
        self.message_user(request, f"{updated} customer(s) suspended.", messages.SUCCESS)
    suspend_customers.short_description = "Suspend selected customers"

    def unsuspend_customers(self, request, queryset):
        updated = queryset.update(is_suspended=False)
        from apps.user_account.models import User
        User.objects.filter(customer_profile__in=queryset).update(is_active=True)
        self.message_user(request, f"{updated} customer(s) unsuspended.", messages.SUCCESS)
    unsuspend_customers.short_description = "Unsuspend selected customers"

    def delete_customers(self, request, queryset):
        from apps.user_account.models import User
        user_ids = list(queryset.values_list("user_id", flat=True))
        User.objects.filter(id__in=user_ids).update(is_active=False, is_deleted=True)
        updated = queryset.update(is_active=False, is_deleted=True)
        self.message_user(request, f"{updated} customer(s) deleted.", messages.SUCCESS)
    delete_customers.short_description = "Soft delete selected customers"


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ("customer", "product", "created_at")
    search_fields = ("customer__user__email", "product__name_en")
