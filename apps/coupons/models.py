from django.db import models

from core.base_models import BaseModel
from core.choices import CouponTypeChoices, RegionChoices, StatusChoices


class Coupon(BaseModel):
    coupon_code = models.CharField(max_length=50, unique=True, db_index=True)
    coupon_type = models.CharField(max_length=16, choices=CouponTypeChoices.choices, db_index=True)
    coupon_value = models.DecimalField(max_digits=12, decimal_places=2)
    valid_from = models.DateTimeField(db_index=True)
    valid_until = models.DateTimeField(db_index=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    region = models.CharField(max_length=16, choices=RegionChoices.choices, db_index=True)
    status = models.CharField(max_length=16, choices=StatusChoices.choices, default=StatusChoices.ACTIVE, db_index=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("coupon_code", "status")),
            models.Index(fields=("region", "valid_until")),
        ]

    def save(self, *args, **kwargs):
        if self.valid_until:
            if self.valid_until.hour == 0 and self.valid_until.minute == 0 and self.valid_until.second == 0:
                self.valid_until = self.valid_until.replace(hour=23, minute=59, second=59, microsecond=999999)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.coupon_code


class CouponUsage(BaseModel):
    """
    Tracks which customers have used which coupons.
    Ensures each customer can only use a specific coupon once.
    """
    coupon = models.ForeignKey(
        "coupons.Coupon",
        on_delete=models.CASCADE,
        related_name="usage_records",
    )
    customer = models.ForeignKey(
        "customers.CustomerProfile",
        on_delete=models.CASCADE,
        related_name="coupon_usage_records",
    )
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="coupon_usage_records",
    )
    used_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-used_at",)
        unique_together = [("coupon", "customer")]  # Ensures one coupon per customer
        indexes = [
            models.Index(fields=("coupon", "customer")),
            models.Index(fields=("customer", "used_at")),
        ]

    def __str__(self):
        return f"{self.customer} used {self.coupon.coupon_code}"


class Offer(BaseModel):
    warehouse = models.ForeignKey(
        "warehouses.Warehouse",
        on_delete=models.CASCADE,
        related_name="offers",
    )
    heading_en = models.CharField(max_length=255)
    heading_ar = models.CharField(max_length=255, null=True, blank=True)
    sub_heading_en = models.CharField(max_length=255, blank=True, default="")
    sub_heading_ar = models.CharField(max_length=255, null=True, blank=True, default="")
    image = models.FileField(upload_to="offers/images/", null=True, blank=True)
    cta_button_en = models.CharField(max_length=100)
    cta_button_ar = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=16, choices=StatusChoices.choices, default=StatusChoices.ACTIVE, db_index=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("warehouse", "status")),
        ]

    def __str__(self):
        return self.heading_en
