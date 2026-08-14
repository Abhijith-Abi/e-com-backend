from django.contrib import admin

from apps.banners.models import Banner


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ("headline_en", "warehouse", "device", "status", "image")
    search_fields = ("headline_en", "headline_ar")
    list_filter = ("device", "status", "warehouse")
    ordering = ("-created_at",)
    fields = (
        "warehouse",
        "headline_en", "headline_ar",
        "sub_text_en", "sub_text_ar",
        "sub_paragraph_en", "sub_paragraph_ar",
        "cta_label_en", "cta_label_ar",
        "image", "link",
        "device", "status",
        "is_active",
    )
