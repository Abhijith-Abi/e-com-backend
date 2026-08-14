from django.db import models

from core.base_models import BaseModel


class Cart(BaseModel):
    customer = models.OneToOneField(
        "customers.CustomerProfile",
        on_delete=models.CASCADE,
        related_name="cart",
    )

    class Meta:
        ordering = ("-updated_at",)

    def __str__(self):
        return f"Cart - {self.customer}"


class CartItem(BaseModel):
    cart = models.ForeignKey(
        "cart.Cart",
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="cart_items",
    )
    quantity = models.PositiveIntegerField(default=1)
    price_snapshot = models.DecimalField(max_digits=12, decimal_places=2)
    selected_color = models.CharField(max_length=100, blank=True, default="")
    selected_size = models.CharField(max_length=50, blank=True, default="")

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(fields=("cart", "product", "selected_color", "selected_size"), name="unique_cart_product_variant"),
        ]
        indexes = [
            models.Index(fields=("cart", "product")),
        ]

    def __str__(self):
        return f"{self.product} x {self.quantity}"
