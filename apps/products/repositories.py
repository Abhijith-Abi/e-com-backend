from django.db import models

from apps.products.models import Product, ProductImage
from core.choices import ProductStatusChoices


class ProductRepository:
    @staticmethod
    def list_products():
        return (
            Product.objects.select_related("category", "sub_category", "warehouse")
            .prefetch_related("images")
            .order_by("-created_at")
        )

    @staticmethod
    def list_products_by_warehouse(warehouse_id):
        return (
            Product.objects.select_related("category", "sub_category", "warehouse")
            .prefetch_related("images")
            .filter(warehouse_id=warehouse_id, is_deleted=False)
            .order_by("-created_at")
        )


    @staticmethod
    def list_new_products(days=7):
        from datetime import timedelta
        from django.utils import timezone
        since = timezone.now() - timedelta(days=days)
        return (
            Product.objects.select_related("category", "sub_category", "warehouse")
            .prefetch_related("images")
            .filter(created_at__gte=since, is_active=True, is_deleted=False, status=ProductStatusChoices.ACTIVE)
            .order_by("-created_at")
        )

    @staticmethod
    def list_new_products_by_warehouse(warehouse_id, days=7):
        from datetime import timedelta
        from django.utils import timezone
        since = timezone.now() - timedelta(days=days)
        return (
            Product.objects.select_related("category", "sub_category", "warehouse")
            .prefetch_related("images")
            .filter(warehouse_id=warehouse_id, created_at__gte=since, is_active=True, is_deleted=False, status=ProductStatusChoices.ACTIVE)
            .order_by("-created_at")
        )

    @staticmethod
    def get_product_for_cart(product_id):
        return Product.objects.filter(id=product_id, is_active=True, is_deleted=False).first()

    @staticmethod
    def list_best_sellers_by_warehouse(warehouse_id, months=2, limit=10):
        from datetime import timedelta
        from django.db.models import Sum
        from django.utils import timezone
        since = timezone.now() - timedelta(days=months * 30)
        return (
            Product.objects.select_related("category", "sub_category", "warehouse")
            .prefetch_related("images")
            .filter(warehouse_id=warehouse_id, is_active=True, is_deleted=False)
            .annotate(
                total_sold=Sum(
                    "order_items__quantity",
                    filter=models.Q(
                        order_items__order__created_at__gte=since,
                        order_items__order__warehouse_id=warehouse_id,
                    ),
                )
            )
            .filter(total_sold__isnull=False)
            .order_by("-total_sold")[:limit]
        )


class ProductImageRepository:
    @staticmethod
    def list_images():
        return ProductImage.objects.select_related("product").order_by("-is_primary", "created_at")
