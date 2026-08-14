from django.db import models
from django.utils.text import slugify

from core.base_models import BaseModel
from core.choices import StatusChoices


class Category(BaseModel):
    warehouse = models.ForeignKey(
        "warehouses.Warehouse",
        on_delete=models.PROTECT,
        related_name="categories",
        null=True,
        blank=True,
        db_index=True,
        help_text="If set, this category belongs to a specific warehouse. If null, it is global.",
    )
    name_en = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255, null=True, blank=True)
    slug = models.SlugField(max_length=255, unique=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        related_name="children",
        null=True,
        blank=True,
    )
    status = models.CharField(max_length=16, choices=StatusChoices.choices, default=StatusChoices.ACTIVE, db_index=True)
    image = models.FileField(upload_to="categories/images/", null=True, blank=True)
    is_major = models.BooleanField(default=False, db_index=True)
    sub_heading = models.CharField(max_length=255, null=True, blank=True)
    sub_heading_ar = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("status", "parent")),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name_en)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name_en
