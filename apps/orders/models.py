from django.db import models

from core.base_models import BaseModel
from core.choices import CurrencyChoices, OrderStatusChoices, PaymentStatusChoices


class Order(BaseModel):
    order_id = models.CharField(max_length=32, unique=True, db_index=True)
    customer = models.ForeignKey(
        "customers.CustomerProfile",
        on_delete=models.PROTECT,
        related_name="orders",
    )
    shipping_address = models.ForeignKey(
        "customers.CustomerAddress",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    warehouse = models.ForeignKey(
        "warehouses.Warehouse",
        on_delete=models.PROTECT,
        related_name="orders",
    )
    courier = models.ForeignKey(
        "couriers.Courier",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    tracking_number = models.CharField(max_length=100, null=True, blank=True)
    currency = models.CharField(max_length=3, choices=CurrencyChoices.choices, db_index=True)
    applied_coupon = models.ForeignKey(
        "coupons.Coupon",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    points_redeemed = models.PositiveIntegerField(
        default=0,
        help_text="Number of loyalty points redeemed on this order",
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    # tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gst = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="GST amount (18%)")

    payment_status = models.CharField(
        max_length=16,
        choices=PaymentStatusChoices.choices,
        default=PaymentStatusChoices.PENDING,
        db_index=True,
    )
    order_status = models.CharField(
        max_length=16,
        choices=OrderStatusChoices.choices,
        default=OrderStatusChoices.PENDING,
        db_index=True,
    )
    notes = models.TextField(blank=True, default="", help_text="Additional notes or cancellation reasons")
    cancelled_by = models.CharField(
        max_length=16,
        choices=[("admin", "Admin"), ("user", "User")],
        null=True,
        blank=True,
        help_text="Who cancelled the order"
    )
    cancellation_reason = models.TextField(
        null=True,
        blank=True,
        help_text="Reason for cancellation"
    )
    applied_gift_card = models.ForeignKey(
        "gift_cards.GiftCard",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    gift_card_discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    applied_gift_wrap = models.ForeignKey(
        "gift_cards.GiftCardWrap",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    gift_wrap_charges = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("customer", "created_at")),
            models.Index(fields=("payment_status", "order_status")),
        ]

    def __str__(self):
        return self.order_id

    def save(self, *args, **kwargs):
        if self.courier_id and self.order_status == OrderStatusChoices.PENDING:
            self.order_status = OrderStatusChoices.PROCESSING
        is_new = self._state.adding
        old_order_status = None
        old_payment_status = None
        if not is_new:
            try:
                row = Order.objects.filter(pk=self.pk).values_list("order_status", "payment_status").first()
                if row:
                    old_order_status, old_payment_status = row
            except Exception:
                pass
        super().save(*args, **kwargs)
        if is_new or old_order_status != self.order_status:
            OrderStatusHistory.objects.get_or_create(order=self, status=self.order_status)
            if self.order_status == OrderStatusChoices.CONFIRMED:
                from django.db import transaction
                from apps.orders.emails import send_order_confirmed_email
                transaction.on_commit(lambda: send_order_confirmed_email(self))
        if is_new or old_payment_status != self.payment_status:
            PaymentStatusHistory.objects.get_or_create(order=self, status=self.payment_status)


class OrderItem(BaseModel):
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="order_items",
    )
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    selected_color = models.CharField(max_length=100, blank=True, default="")
    selected_size = models.CharField(max_length=50, blank=True, default="")

    class Meta:
        ordering = ("created_at",)

    def __str__(self):
        return f"{self.order.order_id} - {self.product.sku}"


# Tracks when each status was first reached for an order
ORDER_STATUS_SEQUENCE = [
    "confirmed", "processing", "shipped", "delivered", "cancelled"
]

PAYMENT_STATUS_SEQUENCE = [
    "pending", "authorized", "paid", "failed", "refunded"
]


class OrderStatusHistory(BaseModel):
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="status_history",
    )
    status = models.CharField(max_length=16, choices=OrderStatusChoices.choices, db_index=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("changed_at",)
        unique_together = ("order", "status")

    def __str__(self):
        return f"{self.order.order_id} -> {self.status} at {self.changed_at}"


class PaymentStatusHistory(BaseModel):
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="payment_history",
    )
    status = models.CharField(max_length=16, choices=PaymentStatusChoices.choices, db_index=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("changed_at",)
        unique_together = ("order", "status")

    def __str__(self):
        return f"{self.order.order_id} -> {self.status} at {self.changed_at}"
