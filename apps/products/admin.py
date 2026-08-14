from django import forms
from django.contrib import admin

from apps.products.models import Product, ProductImage
from apps.products.models import Product, ProductImage, LowStockNotification


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        stock = cleaned_data.get("stock")
        low_stock_threshold = cleaned_data.get("low_stock_threshold")

        if stock is not None and stock < 0:
            self.add_error("stock", "Stock cannot be negative.")

        if low_stock_threshold is not None and low_stock_threshold < 0:
            self.add_error("low_stock_threshold", "Low stock threshold cannot be negative.")

        if stock is not None and low_stock_threshold is not None:
            if low_stock_threshold >= stock and stock > 0:
                self.add_error(
                    "low_stock_threshold",
                    f"Low stock threshold ({low_stock_threshold}) must be less than stock ({stock})."
                )

        return cleaned_data


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = ("name_en", "sku", "warehouse", "status", "stock", "required_points", "is_featured")
    search_fields = ("name_en", "name_ar", "sku")
    list_filter = ("status", "type", "is_featured", "category", "warehouse")
    inlines = [ProductImageInline]
    
    fieldsets = (
        ("Basic Information", {
            "fields": ("warehouse", "name_en", "name_ar", "description_en", "description_ar", "sku", "type", "status", "is_featured")
        }),
        ("Category", {
            "fields": ("category", "sub_category")
        }),
        ("Pricing (INR)", {
            "fields": ("price_inr", "sale_price_inr")
        }),
        ("Pricing (GBP)", {
            "fields": ("price_gbp", "sale_price_gbp")
        }),
        ("Pricing (USD)", {
            "fields": ("price_usd", "sale_price_usd")
        }),
        ("Inventory", {
            "fields": ("stock", "low_stock_threshold", "weight")
        }),
        ("Variants", {
            "fields": ("sizes", "colors")
        }),
        ("Loyalty Points", {
            "fields": ("required_points",),
            "description": "Points required ALONG WITH cash to purchase this product."
        }),
    )

    def changelist_view(self, request, extra_context=None):
        from django.db.models import F
        from apps.products.models import LowStockNotification
        
        # Count low stock and out of stock products
        low_stock = Product.objects.filter(
            is_deleted=False, is_active=True,
            stock__lte=F("low_stock_threshold"), stock__gt=0
        ).count()
        out_of_stock = Product.objects.filter(is_deleted=False, is_active=True, stock=0).count()
        
        # Count unread notifications
        unread_notifications = LowStockNotification.objects.filter(is_read=False).count()
        
        if out_of_stock:
            self.message_user(request, f"⚠ {out_of_stock} product(s) are out of stock!", level="error")
        if low_stock:
            self.message_user(request, f"⚠ {low_stock} product(s) are running low on stock!", level="warning")
        if unread_notifications:
            self.message_user(
                request, 
                f"🔔 You have {unread_notifications} unread low stock notification(s). Check 'Low Stock Notifications' section.",
                level="info"
            )
        
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "color", "is_primary", "created_at")
    list_filter = ("is_primary", "color")
@admin.register(LowStockNotification)
class LowStockNotificationAdmin(admin.ModelAdmin):
    list_display = ("product", "remaining_stock", "threshold", "message", "is_read", "notified_at")
    list_filter = ("is_read", "notified_at")
    search_fields = ("product__name_en", "product__sku", "message")
    readonly_fields = ("product", "remaining_stock", "threshold", "message", "notified_at")
    list_editable = ("is_read",)
    date_hierarchy = "notified_at"
    
    def has_add_permission(self, request):
        return False  # Notifications are auto-generated
    
    def has_delete_permission(self, request, obj=None):
        return True  # Allow deletion of old notifications
    
    actions = ["mark_as_read", "mark_as_unread"]
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f"{updated} notification(s) marked as read.")
    mark_as_read.short_description = "Mark selected as read"
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f"{updated} notification(s) marked as unread.")
    mark_as_unread.short_description = "Mark selected as unread"
