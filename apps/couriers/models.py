from django.db import models
from core.base_models import BaseModel


class Courier(BaseModel):
    warehouse = models.ForeignKey(
        "warehouses.Warehouse",
        on_delete=models.CASCADE,
        related_name="couriers",
    )
    name = models.CharField(max_length=255)
    tracking_url = models.CharField(max_length=500, blank=True)
    courier_number = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name
