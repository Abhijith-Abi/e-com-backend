from django.db import models

from core.base_models import BaseModel
from core.choices import PaymentMethodChoices, PaymentStatusChoices


class PaymentMethod(BaseModel):
    """Configurable payment methods. is_active controls visibility to customers."""

    code = models.CharField(max_length=32, unique=True, choices=PaymentMethodChoices.choices)
    name = models.CharField(max_length=64)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class Payment(BaseModel):
    order = models.OneToOneField(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="payment",
    )
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.PROTECT,
        related_name="payments",
        db_index=True,
        null=True,
        blank=True,
    )
    payment_status = models.CharField(
        max_length=16,
        choices=PaymentStatusChoices.choices,
        default=PaymentStatusChoices.PENDING,
        db_index=True,
    )
    transaction_id = models.CharField(max_length=128, unique=True, null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("payment_method", "payment_status")),
        ]

    def __str__(self):
        return f"{self.order.order_id} - {self.payment_method}"
