from django.contrib import admin
from django.db import models
from django.utils.html import format_html

from apps.gift_cards.models import GiftCard, GiftCardCategory, GiftCardWrap
from apps.gift_cards.models import (
    GiftCard, 
    GiftCardCategory, 
    GiftCardWrap,
    LowStockGiftCardNotification,
    LowStockGiftCardWrapNotification
)

@admin.register(GiftCardCategory)
class GiftCardCategoryAdmin(admin.ModelAdmin):
    ordering = ("-created_at",)


@admin.register(GiftCardWrap)
class GiftCardWrapAdmin(admin.ModelAdmin):
    ordering = ("-created_at",)
    list_display = ("wrap_name", "warehouse", "units", "reminder_threshold", "stock_status", "status")

    def stock_status(self, obj):
        if obj.reminder_threshold and obj.units <= obj.reminder_threshold:
            return format_html('<span style="color:red; font-weight:bold;">&#9888; Limited Stock</span>')
        return format_html('<span style="color:green;">&#10004; In Stock</span>')
    stock_status.short_description = "Stock Status"


@admin.register(GiftCard)
class GiftCardAdmin(admin.ModelAdmin):
    ordering = ("-created_at",)
    list_display = ("card_name", "warehouse", "category", "units", "reminder_threshold", "stock_status", "status")

    def stock_status(self, obj):
        if obj.reminder_threshold and obj.units <= obj.reminder_threshold:
            return format_html('<span style="color:red; font-weight:bold;">&#9888; Limited Stock</span>')
        return format_html('<span style="color:green;">&#10004; In Stock</span>')
    stock_status.short_description = "Stock Status"

    def changelist_view(self, request, extra_context=None):
        from django.db.models import F
    # Count low stock gift cards and wraps
        low_stock = GiftCard.objects.filter(
            units__lte=F("reminder_threshold"),
            is_deleted=False,
        ).exclude(reminder_threshold=0).count()
            
        low_stock_wraps = GiftCardWrap.objects.filter(
            units__lte=F("reminder_threshold"),
            is_deleted=False,
        ).exclude(reminder_threshold=0).count()
            
        # Count unread notifications
        unread_card_notifications = LowStockGiftCardNotification.objects.filter(is_read=False).count()
        unread_wrap_notifications = LowStockGiftCardWrapNotification.objects.filter(is_read=False).count()
        total_unread = unread_card_notifications + unread_wrap_notifications
            
        total = low_stock + low_stock_wraps
        if total:
            self.message_user(
                request,
                f"⚠ {total} gift card(s)/wrap(s) are running low on stock!",
                level="warning",
            )
        if total_unread:
            self.message_user(
                request,
                f"🔔 You have {total_unread} unread low stock notification(s). Check 'Low Stock Notifications' sections.",
                level="info",
            )
        return super().changelist_view(request, extra_context=extra_context)

@admin.register(LowStockGiftCardNotification)
class LowStockGiftCardNotificationAdmin(admin.ModelAdmin):
    list_display = ("gift_card", "remaining_units", "threshold", "message", "is_read", "notified_at")
    list_filter = ("is_read", "notified_at")
    search_fields = ("gift_card__card_name", "message")
    readonly_fields = ("gift_card", "remaining_units", "threshold", "message", "notified_at")
    list_editable = ("is_read",)
    date_hierarchy = "notified_at"
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return True
    
    actions = ["mark_as_read", "mark_as_unread"]
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f"{updated} notification(s) marked as read.")
    mark_as_read.short_description = "Mark selected as read"
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f"{updated} notification(s) marked as unread.")
    mark_as_unread.short_description = "Mark selected as unread"


@admin.register(LowStockGiftCardWrapNotification)
class LowStockGiftCardWrapNotificationAdmin(admin.ModelAdmin):
    list_display = ("gift_card_wrap", "remaining_units", "threshold", "message", "is_read", "notified_at")
    list_filter = ("is_read", "notified_at")
    search_fields = ("gift_card_wrap__wrap_name", "message")
    readonly_fields = ("gift_card_wrap", "remaining_units", "threshold", "message", "notified_at")
    list_editable = ("is_read",)
    date_hierarchy = "notified_at"
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return True
    
    actions = ["mark_as_read", "mark_as_unread"]
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f"{updated} notification(s) marked as read.")
    mark_as_read.short_description = "Mark selected as read"
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f"{updated} notification(s) marked as unread.")
    mark_as_unread.short_description = "Mark selected as unread"
