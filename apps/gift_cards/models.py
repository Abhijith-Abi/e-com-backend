from django.db import models

from core.base_models import BaseModel
from core.choices import StatusChoices


class GiftCardCategory(BaseModel):
    warehouse = models.ForeignKey(
        "warehouses.Warehouse",
        on_delete=models.CASCADE,
        related_name="gift_card_categories",
        db_index=True,
    )
    name = models.CharField(max_length=255)
    cards = models.PositiveIntegerField(default=0, help_text="Number of cards in this category")

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(fields=("warehouse", "name"), name="unique_gift_card_category_per_warehouse"),
        ]

    def __str__(self):
        return self.name


class GiftCardWrap(BaseModel):
    warehouse = models.ForeignKey(
        "warehouses.Warehouse",
        on_delete=models.CASCADE,
        related_name="gift_card_wraps",
        db_index=True,
    )
    wrap_name = models.CharField(max_length=255)
    image = models.FileField(upload_to="gift_cards/wraps/", null=True, blank=True)
    units = models.PositiveIntegerField(default=0)
    reminder_threshold = models.PositiveIntegerField(default=0)
    price_inr = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    price_gbp = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    price_usd = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    status = models.CharField(
        max_length=16,
        choices=StatusChoices.choices,
        default=StatusChoices.ACTIVE,
        db_index=True,
    )

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(fields=("warehouse", "wrap_name"), name="unique_gift_card_wrap_per_warehouse"),
        ]
        indexes = [
            models.Index(fields=("warehouse", "status")),
        ]

    def __str__(self):
        return self.wrap_name


class GiftCard(BaseModel):
    warehouse = models.ForeignKey(
        "warehouses.Warehouse",
        on_delete=models.CASCADE,
        related_name="gift_cards",
        db_index=True,
    )
    card_name = models.CharField(max_length=255)
    image = models.FileField(upload_to="gift_cards/images/", null=True, blank=True)
    category = models.ForeignKey(
        GiftCardCategory,
        on_delete=models.PROTECT,
        related_name="gift_cards",
        db_index=True,
    )
    units = models.PositiveIntegerField(default=0)
    reminder_threshold = models.PositiveIntegerField(default=0)
    price_inr = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    price_gbp = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    price_usd = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    status = models.CharField(
        max_length=16,
        choices=StatusChoices.choices,
        default=StatusChoices.ACTIVE,
        db_index=True,
    )

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(fields=("warehouse", "card_name"), name="unique_gift_card_per_warehouse"),
        ]
        indexes = [
            models.Index(fields=("warehouse", "status")),
            models.Index(fields=("category", "status")),
        ]

    def __str__(self):
        return self.card_name
class LowStockGiftCardNotification(BaseModel):
    gift_card = models.ForeignKey(
        "gift_cards.GiftCard",
        on_delete=models.CASCADE,
        related_name="low_stock_notifications",
    )
    remaining_units = models.PositiveIntegerField()
    threshold = models.PositiveIntegerField()
    message = models.CharField(max_length=500)
    is_read = models.BooleanField(default=False, db_index=True)
    notified_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-notified_at",)
        indexes = [
            models.Index(fields=("is_read", "notified_at")),
        ]

    def __str__(self):
        return f"Low Stock Alert: {self.gift_card.card_name} - {self.remaining_units} left"


class LowStockGiftCardWrapNotification(BaseModel):
    gift_card_wrap = models.ForeignKey(
        "gift_cards.GiftCardWrap",
        on_delete=models.CASCADE,
        related_name="low_stock_notifications",
    )
    remaining_units = models.PositiveIntegerField()
    threshold = models.PositiveIntegerField()
    message = models.CharField(max_length=500)
    is_read = models.BooleanField(default=False, db_index=True)
    notified_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-notified_at",)
        indexes = [
            models.Index(fields=("is_read", "notified_at")),
        ]

    def __str__(self):
        return f"Low Stock Alert: {self.gift_card_wrap.wrap_name} - {self.remaining_units} left"
