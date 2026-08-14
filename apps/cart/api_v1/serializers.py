from rest_framework import serializers

from apps.cart.models import Cart, CartItem


class RedeemSettingsSerializer(serializers.Serializer):
    """Serializer for RedeemSettings to include in cart response"""
    id = serializers.UUIDField()
    points_per_currency_unit = serializers.DecimalField(max_digits=8, decimal_places=4)
    min_points_to_redeem = serializers.IntegerField()
    max_redeem_percent = serializers.IntegerField()
    is_active = serializers.BooleanField()


class CartItemProductSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name_en = serializers.CharField()
    name_ar = serializers.CharField()
    sku = serializers.CharField()
    stock = serializers.SerializerMethodField()
    price_inr = serializers.DecimalField(max_digits=12, decimal_places=2)
    price_gbp = serializers.DecimalField(max_digits=12, decimal_places=2)
    price_usd = serializers.DecimalField(max_digits=12, decimal_places=2)
    sale_price_inr = serializers.DecimalField(max_digits=12, decimal_places=2)
    sale_price_gbp = serializers.DecimalField(max_digits=12, decimal_places=2)
    sale_price_usd = serializers.DecimalField(max_digits=12, decimal_places=2)
    required_points = serializers.IntegerField()
    image = serializers.SerializerMethodField()
    sizes = serializers.SerializerMethodField()

    def get_image(self, product):
        images = list(product.images.all())
        selected_color = self.context.get("selected_color", "")
        if selected_color:
            img = next((i for i in images if i.color == selected_color), None)
        else:
            img = next((i for i in images if i.is_primary), images[0] if images else None)
        if img is None:
            return None
        request = self.context.get("request")
        url = img.image.url if img.image else None
        return {
            "id": str(img.id),
            "url": request.build_absolute_uri(url) if request and url else url,
            "color": img.color,
        }

    def get_stock(self, product):
        selected_color = self.context.get("selected_color", "")
        selected_size = self.context.get("selected_size", "")
        
        images = list(product.images.all())
        
        if selected_color:
            variant = next((i for i in images if i.color == selected_color), None)
        else:
            variant = next((i for i in images if i.is_primary), images[0] if images else None)
            
        if variant:
            if selected_size and variant.sizes:
                for size_data in variant.sizes:
                    if size_data.get('size') == selected_size:
                        return size_data.get('stock', 0)
            return variant.stock
                
        return product.stock
        
    def get_sizes(self, product):
        selected_color = self.context.get("selected_color", "")
        images = list(product.images.all())
        
        if selected_color:
            variant = next((i for i in images if i.color == selected_color), None)
        else:
            variant = next((i for i in images if i.is_primary), images[0] if images else None)
            
        if variant and variant.sizes:
            return variant.sizes
            
        return product.sizes


class CartItemSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()

    def get_product(self, item):
        serializer = CartItemProductSerializer(
            item.product,
            context={
                **self.context, 
                "selected_color": item.selected_color,
                "selected_size": item.selected_size
            }
        )
        return serializer.data

    class Meta:
        model = CartItem
        fields = ("id", "product", "quantity", "selected_color", "selected_size", "created_at", "updated_at")


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    subtotal = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()
    cart_count = serializers.SerializerMethodField()
    total_required_points = serializers.SerializerMethodField()
    redeem_settings = serializers.SerializerMethodField()

    def get_subtotal(self, cart):
        from decimal import Decimal
        return sum((item.price_snapshot * item.quantity for item in cart.items.all()), Decimal("0.00"))

    def get_total_amount(self, cart):
        from decimal import Decimal
        subtotal = self.get_subtotal(cart)
        gst = (subtotal * Decimal("0.18")).quantize(Decimal("0.01"))
        return (subtotal + gst).quantize(Decimal("0.01"))

    def get_cart_count(self, cart):
        return cart.items.count()

    def get_total_required_points(self, cart):
        """Calculate total points required for all items in cart"""
        total_points = 0
        for item in cart.items.select_related('product').all():
            total_points += (item.product.required_points * item.quantity)
        return total_points

    def get_redeem_settings(self, cart):
        """Get active redeem settings for points redemption configuration"""
        from apps.redeem.models import RedeemSettings
        try:
            settings = RedeemSettings.objects.filter(is_active=True).first()
            if settings:
                return RedeemSettingsSerializer(settings).data
            return None
        except:
            return None

    class Meta:
        model = Cart
        fields = ("id", "items", "subtotal", "total_amount", "cart_count", "total_required_points", "redeem_settings")
