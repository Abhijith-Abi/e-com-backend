class ProductService:
    @staticmethod
    def decrement_stock(product, quantity, selected_color=None, selected_size=None):
        product.stock = max(product.stock - quantity, 0)
        product.save(update_fields=["stock", "updated_at"])
        
        # Decrement variant stock
        from apps.products.models import ProductImage
        if selected_color:
            variant = ProductImage.objects.filter(product=product, color=selected_color).first()
        else:
            variant = ProductImage.objects.filter(product=product, is_primary=True).first()
            if not variant:
                variant = ProductImage.objects.filter(product=product).first()
                
        if variant:
            variant.stock = max(variant.stock - quantity, 0)
                
            # Decrement size-specific stock if a size is selected
            if selected_size and variant.sizes:
                updated_sizes = []
                for size_data in variant.sizes:
                    if size_data.get('size') == selected_size:
                        current_stock = size_data.get('stock', 0)
                        size_data['stock'] = max(current_stock - quantity, 0)
                    updated_sizes.append(size_data)
                variant.sizes = updated_sizes
            
            variant.save(update_fields=["stock", "sizes", "updated_at"])

        # Check if stock is low and create notification
        ProductService.check_and_create_low_stock_notification(product)

    @staticmethod
    def increment_stock(product, quantity, selected_color=None, selected_size=None):
        product.stock += quantity
        product.save(update_fields=["stock", "updated_at"])
        
        # Increment variant stock
        from apps.products.models import ProductImage
        if selected_color:
            variant = ProductImage.objects.filter(product=product, color=selected_color).first()
        else:
            variant = ProductImage.objects.filter(product=product, is_primary=True).first()
            if not variant:
                variant = ProductImage.objects.filter(product=product).first()
                
        if variant:
            variant.stock += quantity
                
            # Increment size-specific stock if a size is selected
            if selected_size and variant.sizes:
                updated_sizes = []
                for size_data in variant.sizes:
                    if size_data.get('size') == selected_size:
                        current_stock = size_data.get('stock', 0)
                        size_data['stock'] = current_stock + quantity
                    updated_sizes.append(size_data)
                variant.sizes = updated_sizes
            
            variant.save(update_fields=["stock", "sizes", "updated_at"])

    @staticmethod
    def check_and_create_low_stock_notification(product):
        """
        Create a low stock notification if stock falls below or equals threshold
        """
        from apps.products.models import LowStockNotification
        
        if product.stock <= product.low_stock_threshold and product.stock > 0:
            # Check if there's already an unread notification for this stock level
            existing = LowStockNotification.objects.filter(
                product=product,
                remaining_stock=product.stock,
                is_read=False
            ).exists()
            
            if not existing:
                message = f"{product.name_en} has {product.stock} stock(s) left"
                LowStockNotification.objects.create(
                    product=product,
                    remaining_stock=product.stock,
                    threshold=product.low_stock_threshold,
                    message=message
                )
        elif product.stock == 0:
            # Out of stock notification
            existing = LowStockNotification.objects.filter(
                product=product,
                remaining_stock=0,
                is_read=False
            ).exists()
            
            if not existing:
                message = f"{product.name_en} is OUT OF STOCK"
                LowStockNotification.objects.create(
                    product=product,
                    remaining_stock=0,
                    threshold=product.low_stock_threshold,
                    message=message
                )
