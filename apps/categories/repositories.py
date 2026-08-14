from django.db.models import Count, Q, Max, Case, When, Value, IntegerField
from django.db.models.functions import Coalesce

from apps.categories.models import Category


class CategoryRepository:
    @staticmethod
    def list_categories():
        return (
            Category.objects.select_related("parent", "warehouse")
            .prefetch_related("children")
            .annotate(
                direct_product_count=Count(
                    "products", filter=Q(products__is_deleted=False), distinct=True
                ) + Count(
                    "sub_category_products", filter=Q(sub_category_products__is_deleted=False), distinct=True
                ),
                child_product_count=Count(
                    "children__products",
                    filter=Q(children__products__is_deleted=False),
                    distinct=True,
                ) + Count(
                    "children__sub_category_products",
                    filter=Q(children__sub_category_products__is_deleted=False),
                    distinct=True,
                ),
                latest_activity=Coalesce(Max("children__created_at"), "created_at"),
                is_child=Case(
                    When(parent__isnull=True, then=Value(0)),
                    default=Value(1),
                    output_field=IntegerField()
                )
            )
            .order_by("-latest_activity", "is_child", "-created_at")     
        )

    @staticmethod
    def list_categories_by_warehouse(warehouse_id):
        return (
            Category.objects.select_related("parent", "warehouse")
            .prefetch_related("children")
            .filter(warehouse_id=warehouse_id)
            .annotate(
                direct_product_count=Count(
                    "products", filter=Q(products__is_deleted=False), distinct=True
                ) + Count(
                    "sub_category_products", filter=Q(sub_category_products__is_deleted=False), distinct=True
                ),
                child_product_count=Count(
                    "children__products",
                    filter=Q(children__products__is_deleted=False),
                    distinct=True,
                ) + Count(
                    "children__sub_category_products",
                    filter=Q(children__sub_category_products__is_deleted=False),
                    distinct=True,
                ),
                latest_activity=Coalesce(Max("children__created_at"), "created_at"),
                is_child=Case(
                    When(parent__isnull=True, then=Value(0)),
                    default=Value(1),
                    output_field=IntegerField()
                )
            )
            .order_by("-latest_activity", "is_child", "-created_at")
        )