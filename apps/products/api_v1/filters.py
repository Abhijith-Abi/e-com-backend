import django_filters
from apps.products.models import Product


class ProductFilter(django_filters.FilterSet):
    category_name = django_filters.CharFilter(
        field_name="category__name_en",
        lookup_expr="istartswith",
        label="Filter by category name (starts with)",
    )
    sub_category_name = django_filters.CharFilter(
        field_name="sub_category__name_en",
        lookup_expr="istartswith",
        label="Filter by sub-category name (starts with)",
    )
    tag = django_filters.CharFilter(
        method="filter_by_tag",
        label="Filter by category or sub-category name (exact case-insensitive)",
    )

    class Meta:
        model = Product
        fields = ("category", "sub_category", "status", "is_featured", "type", "warehouse")

    def filter_by_tag(self, queryset, name, value):
        from django.db.models import Q
        return queryset.filter(
            Q(category__name_en__iexact=value) | Q(sub_category__name_en__iexact=value)
        )
