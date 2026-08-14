from django.db import models

from core.base_models import BaseModel
from core.choices import DeviceChoices, StatusChoices


class Testimonial(BaseModel):
    warehouse = models.ForeignKey(
        "warehouses.Warehouse",
        on_delete=models.CASCADE,
        related_name="testimonials",
    )
    name_en = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255, null=True, blank=True)
    review_en = models.TextField()
    review_ar = models.TextField(null=True, blank=True)
    content_en = models.TextField(blank=True)
    content_ar = models.TextField(null=True, blank=True)
    city_en = models.CharField(max_length=100)
    city_ar = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=16, choices=StatusChoices.choices, default=StatusChoices.ACTIVE, db_index=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.name_en
    def save(self, *args, **kwargs):
    # Automatically sync is_active with status field
        if self.status == 'active':
            self.is_active = True
        else:
            self.is_active = False
    

        super().save(*args, **kwargs)


class Banner(BaseModel):
    warehouse = models.ForeignKey(
        "warehouses.Warehouse",
        on_delete=models.CASCADE,
        related_name="banners",
    )
    headline_en = models.CharField(max_length=255)
    headline_ar = models.CharField(max_length=255, null=True, blank=True)
    sub_text_en = models.TextField(blank=True)
    sub_text_ar = models.TextField(null=True, blank=True)
    sub_paragraph_en = models.TextField(blank=True)
    sub_paragraph_ar = models.TextField(null=True, blank=True)
    cta_label_en = models.CharField(max_length=100)
    cta_label_ar = models.CharField(max_length=100, null=True, blank=True)
    image = models.FileField(upload_to="banners/images/", null=True, blank=True)
    link = models.CharField(max_length=500, blank=True, default="")
    device = models.CharField(max_length=16, choices=DeviceChoices.choices, default=DeviceChoices.BOTH, db_index=True)
    status = models.CharField(max_length=16, choices=StatusChoices.choices, default=StatusChoices.ACTIVE, db_index=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("device", "status")),
        ]

    def __str__(self):
        return self.headline_en
    
    def save(self, *args, **kwargs):
        # Automatically sync is_active with status field
        if self.status == 'active':
            self.is_active = True
        else:
            self.is_active = False
        
        super().save(*args, **kwargs)
