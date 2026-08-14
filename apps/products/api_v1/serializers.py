from rest_framework import serializers

from apps.products.models import Product, ProductImage


class ProductImageSerializer(serializers.ModelSerializer):
    delete_image = serializers.BooleanField(write_only=True, required=False, default=False)

    class Meta:
        model = ProductImage
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")

    def create(self, validated_data):
        validated_data.pop("delete_image", None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        delete_image = validated_data.pop("delete_image", False)
        if not delete_image and "image" not in validated_data:
            validated_data["image"] = instance.image
        elif delete_image:
            if instance.image:
                instance.image.delete(save=False)
            validated_data.pop("image", None)
        return super().update(instance, validated_data)


class BulkProductImageSerializer(serializers.Serializer):
    """
    Upload multiple images for a product, optionally tagged to a color.

    multipart/form-data fields:
      - product    : <uuid>
      - color      : "Red"       (optional)
      - is_primary : true/false  (optional, marks first image as primary)
      - images     : <file> ...  (repeated key)
    """
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    color = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    is_primary = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        request = self.context.get("request")
        files = request.FILES.getlist("images") if request else []
        if not files:
            raise serializers.ValidationError({"images": "At least one image file is required."})

        color = attrs.get("color", "")
        if color:
            product_colors = attrs["product"].colors or []
            if color not in product_colors:
                raise serializers.ValidationError(
                    {"color": f"'{color}' is not a valid color for this product. Available: {product_colors}"}
                )

        attrs["images"] = files
        return attrs

    def create(self, validated_data):
        product = validated_data["product"]
        color = validated_data.get("color", "")
        is_primary = validated_data.get("is_primary", False)
        created = []
        for idx, img in enumerate(validated_data["images"]):
            obj = ProductImage.objects.create(
                product=product,
                image=img,
                color=color,
                is_primary=(is_primary and idx == 0),
            )
            created.append(obj)
        return created


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    warehouse_name = serializers.CharField(source="warehouse.warehouse_name", read_only=True)
    category_name = serializers.CharField(source="category.name_en", read_only=True)
    category_name_ar = serializers.CharField(source="category.name_ar", read_only=True)
    sub_category_name = serializers.CharField(source="sub_category.name_en", read_only=True, default=None)     
    sub_category_name_ar = serializers.CharField(source="sub_category.name_ar", read_only=True, default=None)  
    gst_amount_inr = serializers.SerializerMethodField()
    price_inr_with_gst = serializers.SerializerMethodField()
    redeem_settings = serializers.SerializerMethodField()
    total_stock = serializers.SerializerMethodField()

    def get_total_stock(self, obj):
        total_stock = 0
        for img in obj.images.all():
            if img.sizes:
                for size_data in img.sizes:
                    if isinstance(size_data, dict):
                        total_stock += size_data.get("stock", 0)
            else:
                total_stock += getattr(img, "stock", 0)
        return total_stock


    def get_gst_amount_inr(self, obj):
        from decimal import Decimal
        price = obj.sale_price_inr or obj.price_inr
        if price is None:
            return None
        return round(float(price) * 0.18, 2)

    def get_price_inr_with_gst(self, obj):
        from decimal import Decimal
        price = obj.sale_price_inr or obj.price_inr
        if price is None:
            return None
        return round(float(price) * 1.18, 2)
    def get_redeem_settings(self, obj):
        from apps.redeem.repositories import RedeemSettingsRepository
        from apps.redeem.api_v1.serializers import RedeemSettingsSerializer
        
        settings = RedeemSettingsRepository.get_active()
        if settings:
            return RedeemSettingsSerializer(settings).data
        return None


    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")


class WarehouseScopedProductSerializer(ProductSerializer):
    """Used by warehouse-scoped endpoint — warehouse is set from URL, not request body."""
    class Meta(ProductSerializer.Meta):
        read_only_fields = ("id", "warehouse", "created_at", "updated_at")


class BestSellerProductSerializer(WarehouseScopedProductSerializer):
    total_sold = serializers.IntegerField(read_only=True)

    class Meta(WarehouseScopedProductSerializer.Meta):
        fields = "__all__"
        read_only_fields = ("id", "warehouse", "created_at", "updated_at")


class NewProductSerializer(serializers.ModelSerializer):
    category_id = serializers.UUIDField(source="category.id", read_only=True)
    category_name = serializers.CharField(source="category.name_en", read_only=True)
    primary_image = serializers.SerializerMethodField()
    warehouse_name = serializers.CharField(source="warehouse.warehouse_name", read_only=True)
    gst_amount_inr = serializers.SerializerMethodField()
    price_inr_with_gst = serializers.SerializerMethodField()
    redeem_settings = serializers.SerializerMethodField()
    stock = serializers.IntegerField(read_only=True)
    total_stock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id", "name_en", "name_ar",
            "sku", "type", "status", "is_featured",
            "price_inr", "price_gbp", "price_usd",
            "sale_price_inr", "sale_price_gbp", "sale_price_usd",
            "gst_amount_inr", "price_inr_with_gst",
            "category_id", "category_name",
            "warehouse", "warehouse_name",
            "required_points",
            "primary_image", "created_at", "redeem_settings", "stock", "total_stock"
        )

    def get_total_stock(self, obj):
        total_stock = 0
        for img in obj.images.all():
            if img.sizes:
                for size_data in img.sizes:
                    if isinstance(size_data, dict):
                        total_stock += size_data.get("stock", 0)
            else:
                total_stock += getattr(img, "stock", 0)
        return total_stock

    def get_primary_image(self, obj):
        img = next((i for i in obj.images.all() if i.is_primary), None) or next(iter(obj.images.all()), None)
        if img and img.image:
            request = self.context.get("request")
            return request.build_absolute_uri(img.image.url) if request else img.image.url
        return None

    def get_gst_amount_inr(self, obj):
        price = obj.sale_price_inr or obj.price_inr
        if price is None:
            return None
        return round(float(price) * 0.18, 2)

    def get_price_inr_with_gst(self, obj):
        price = obj.sale_price_inr or obj.price_inr
        if price is None:
            return None
        return round(float(price) * 1.18, 2)

    def get_redeem_settings(self, obj):
        from apps.redeem.repositories import RedeemSettingsRepository
        from apps.redeem.api_v1.serializers import RedeemSettingsSerializer

        settings = RedeemSettingsRepository.get_active()
        if settings:
            return RedeemSettingsSerializer(settings).data
        return None
from apps.products.models import LowStockNotification

class LowStockNotificationSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name_en", read_only=True)
    product_sku = serializers.CharField(source="product.sku", read_only=True)

    class Meta:
        model = LowStockNotification
        fields = ["id", "product", "product_name", "product_sku", "remaining_stock", "threshold", "message", "is_read", "notified_at"]