from rest_framework import serializers

from apps.categories.models import Category


class ProductCountMixin:
    def get_product_count(self, obj):
        from django.db.models import Count, Q

        # If annotated by repository, use annotations
        if hasattr(obj, "direct_product_count"):
            direct = getattr(obj, "direct_product_count", 0) or 0
            child = getattr(obj, "child_product_count", 0) or 0
            return direct + child

        # Fallback: calculate directly from DB
        if obj.parent is None:
            # Parent category - only count products in children
            child = 0
            for child_cat in obj.children.all():
                child += child_cat.products.filter(is_deleted=False).count()
                child += child_cat.sub_category_products.filter(is_deleted=False).count()
            return child
        else:
            # Child category - count direct products
            direct = obj.products.filter(is_deleted=False).count()
            direct += obj.sub_category_products.filter(is_deleted=False).count()
            return direct


class CategorySerializer(serializers.ModelSerializer, ProductCountMixin):
    delete_image = serializers.BooleanField(write_only=True, required=False, default=False)
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = "__all__"
        read_only_fields = ("id", "warehouse", "created_at", "updated_at")

    def create(self, validated_data):
        validated_data.pop("delete_image", None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        delete_image = validated_data.pop("delete_image", False)
        if delete_image:
            if instance.image:
                instance.image.delete(save=False)
            validated_data["image"] = None
        elif "image" not in validated_data:
            validated_data["image"] = instance.image
        return super().update(instance, validated_data)


class CategoryChildSerializer(serializers.ModelSerializer, ProductCountMixin):
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ("id", "name_en", "name_ar", "slug", "image", "status", "is_major", "sub_heading", "sub_heading_ar", "product_count")


class CategoryTreeSerializer(serializers.ModelSerializer, ProductCountMixin):
    children = CategoryChildSerializer(many=True, read_only=True)
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ("id", "name_en", "name_ar", "slug", "image", "status", "is_major", "sub_heading", "sub_heading_ar", "product_count", "children")
