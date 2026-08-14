from django.contrib import admin

from apps.categories.models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name_en", "warehouse", "parent", "type", "status", "is_major", "is_active", "product_count")
    search_fields = ("name_en", "name_ar", "slug")
    list_filter = ("status", "is_major", "is_active", "warehouse", "parent")
    list_per_page = 10
    ordering = ("-created_at",)
    prepopulated_fields = {"slug": ("name_en",)}
    readonly_fields = ("image_preview",)

    def get_queryset(self, request):
        from django.db.models import Count, Q
        qs = super().get_queryset(request)
        return qs.annotate(
            direct_product_count=Count("products", filter=Q(products__is_deleted=False)),
            child_product_count=Count("children__products", filter=Q(children__products__is_deleted=False), distinct=True)
        )

    def type(self, obj):
        return "Subcategory" if obj.parent else "Category"
    type.short_description = "Type"

    def product_count(self, obj):
        return getattr(obj, "direct_product_count", 0) + getattr(obj, "child_product_count", 0)
    product_count.short_description = "Products"

    def image_preview(self, obj):
        from django.utils.html import format_html
        if obj.image:
            return format_html('<img src="{}" style="max-height: 100px;" />', obj.image.url)
        return "-"
    image_preview.short_description = "Preview"
