from django.db import models

from core.base_models import BaseModel


class StoreAnalytics(BaseModel):
    total_revenue = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_orders = models.PositiveIntegerField(default=0)
    cancellation_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        verbose_name_plural = "Store analytics"
        ordering = ("-created_at",)

    def __str__(self):
        return f"Revenue {self.total_revenue}"
