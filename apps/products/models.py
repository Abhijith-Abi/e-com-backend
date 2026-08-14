from django.db import models

from core.base_models import BaseModel
from core.choices import ProductStatusChoices, ProductTypeChoices


class Product(BaseModel):
    warehouse = models.ForeignKey(
        "warehouses.Warehouse",
        on_delete=models.PROTECT,
        related_name="products",
    )
    name_en = models.CharField(max_length=255, db_index=True)
    name_ar = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    description_en = models.TextField()
    description_ar = models.TextField(null=True, blank=True)
    category = models.ForeignKey(
        "categories.Category",
        on_delete=models.PROTECT,
        related_name="products",
    )
    sub_category = models.ForeignKey(
        "categories.Category",
        on_delete=models.PROTECT,
        related_name="sub_category_products",
        null=True,
        blank=True,
    )
    type = models.CharField(max_length=16, choices=ProductTypeChoices.choices, default=ProductTypeChoices.PHYSICAL)
    sku = models.CharField(max_length=64, unique=True, db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True)
    status = models.CharField(max_length=20, choices=ProductStatusChoices.choices, default=ProductStatusChoices.DRAFT, db_index=True)
    price_inr = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    price_gbp = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    price_usd = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    sale_price_inr = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    sale_price_gbp = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    sale_price_usd = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    stock = models.PositiveIntegerField(default=0, db_index=True)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    weight = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    sizes = models.JSONField(default=list, blank=True)
    colors = models.JSONField(default=list, blank=True)
    required_points = models.PositiveIntegerField(
        default=0,
        help_text="Points required along with cash to purchase this product (Cash + Points purchase).",
    )
   
    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("status", "is_featured")),
            models.Index(fields=("category", "sub_category")),
            models.Index(fields=("sku", "is_active")),
            models.Index(fields=("warehouse", "status")),
        ]

    def __str__(self):
        return f"{self.name_en} ({self.sku})"


class ProductImage(BaseModel):
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.FileField(upload_to="products/images/")
    is_primary = models.BooleanField(default=False, db_index=True)
    color = models.CharField(max_length=100, blank=True, default="", db_index=True)
    stock = models.IntegerField(default=0, help_text="Total stock for this specific color variant")
    sizes = models.JSONField(default=list, blank=True, help_text="e.g. [{'size': 'M', 'stock': 20}]")

    class Meta:
        ordering = ("-is_primary", "created_at")

    def __str__(self):
        return f"Image for {self.product.sku}"

    def save(self, *args, **kwargs):
        if self.is_primary:
            # Set all other images for this product to is_primary=False
            qs = ProductImage.objects.filter(product=self.product)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            qs.update(is_primary=False)

        super().save(*args, **kwargs)

        # Recalculate parent product total stock from all its images
        total_stock = 0
        for img in ProductImage.objects.filter(product=self.product):
            if img.sizes:
                for size_data in img.sizes:
                    if isinstance(size_data, dict):
                        total_stock += size_data.get("stock", 0)
            else:
                total_stock += img.stock

        self.product.stock = total_stock

        # When an image is added, automatically change product status to ACTIVE if it's in DRAFT
        if self.product.status == ProductStatusChoices.DRAFT:
            self.product.status = ProductStatusChoices.ACTIVE

        self.product.save(update_fields=["stock", "status", "updated_at"])

    def delete(self, *args, **kwargs):
        product = self.product
        super().delete(*args, **kwargs)

        # Recalculate parent product total stock after image deletion
        total_stock = 0
        for img in ProductImage.objects.filter(product=product):
            if img.sizes:
                for size_data in img.sizes:
                    if isinstance(size_data, dict):
                        total_stock += size_data.get("stock", 0)
            else:
                total_stock += img.stock

        product.stock = total_stock
        product.save(update_fields=["stock", "updated_at"])
class LowStockNotification(BaseModel):
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="low_stock_notifications",
    )
    remaining_stock = models.PositiveIntegerField()
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
        return f"Low Stock Alert: {self.product.name_en} - {self.remaining_stock} left"
