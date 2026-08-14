from django.db import models

from core.base_models import BaseModel
from core.choices import RegionChoices


class Warehouse(BaseModel):
    warehouse_name = models.CharField(max_length=255, unique=True)
    warehouse_address = models.TextField()
    warehouse_location = models.CharField(max_length=16, choices=RegionChoices.choices, db_index=True)
    warehouse_details = models.JSONField(default=dict, blank=True)
    delivery_to = models.JSONField(default=list, blank=True)
    flag_image = models.FileField(upload_to="warehouses/flags/", null=True, blank=True)

    class Meta:
        ordering = ("warehouse_name",)
        indexes = [
            models.Index(fields=("warehouse_location", "is_active")),
        ]

    def __str__(self):
        return f"{self.warehouse_name} ({self.warehouse_location})"
