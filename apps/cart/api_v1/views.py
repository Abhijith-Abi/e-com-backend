from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view, inline_serializer
from rest_framework import fields, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.cart.api_v1.serializers import CartItemSerializer, CartSerializer
from apps.cart.repositories import CartItemRepository, CartRepository
from apps.cart.services import CartService
from apps.customers.services import CustomerService
from apps.orders.services import OrderService


@extend_schema_view(
    list=extend_schema(
        tags=["Cart"],
        summary="List carts",
        parameters=[
            OpenApiParameter("customer", description="Filter by customer UUID", required=False),
        ],
    ),
    create=extend_schema(tags=["Cart"], summary="Create a cart"),
    retrieve=extend_schema(tags=["Cart"], summary="Get a cart"),
    update=extend_schema(tags=["Cart"], summary="Update a cart"),
    partial_update=extend_schema(tags=["Cart"], summary="Partially update a cart"),
    destroy=extend_schema(tags=["Cart"], summary="Delete a cart"),
)
class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    queryset = CartRepository.list_carts()
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ("customer",)

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_admin:
            return queryset
        return queryset.filter(customer__user=self.request.user)

    @extend_schema(
        tags=["Cart"],
        summary="Get or create my cart",
        description="Returns the current authenticated user's cart, creating one if it doesn't exist.",
        request=None,
        responses={200: CartSerializer},
    )
    @action(detail=False, methods=["post"])
    def mine(self, request):
        customer = CustomerService.ensure_profile(request.user)
        cart, _ = CartRepository.get_or_create_for_customer(customer)
        serializer = self.get_serializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Cart"],
        summary="Add item to cart",
        description="Adds a product to the current user's cart. Creates the cart if it doesn't exist.",
        request=inline_serializer(
            name="AddCartItemRequest",
            fields={
                "product": fields.UUIDField(help_text="Product UUID"),
                "quantity": fields.IntegerField(default=1, help_text="Quantity to add (default: 1)"),
            },
        ),
        responses={201: CartItemSerializer},
    )
    @action(detail=False, methods=["post"])
    def add_item(self, request):
        customer = CustomerService.ensure_profile(request.user)
        # Accept both "product" and "product_id" keys
        product_id = request.data.get("product") or request.data.get("product_id")
        if not product_id:
            return Response(
                {"error": "product or product_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        item = CartService.add_item(
            customer=customer,
            product_id=product_id,
            quantity=int(request.data.get("quantity", 1)),
            selected_color=request.data.get("selected_color") or request.data.get("color", ""),
            selected_size=request.data.get("selected_size") or request.data.get("size", ""),
        )
        serializer = CartItemSerializer(item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=["Cart"],
        summary="Checkout cart",
        description=(
            "Converts the cart into an order.\n\n"
            "**Address options (pick one):**\n"
            "- `address_id` — UUID of an existing saved address\n"
            "- `new_address` object — creates a new `CustomerAddress` and links it\n"
            "- Neither — uses the customer's default saved address automatically\n\n"
            "**Payment method:** pass `payment_method` code (`cod`, `razorpay`, `stripe`). "
            "Defaults to first active method if omitted."
        ),
        request=inline_serializer(
            name="CheckoutRequest",
            fields={
                "warehouse": fields.UUIDField(help_text="Warehouse UUID (required)"),
                "currency": fields.ChoiceField(
                    choices=["INR", "GBP", "USD"],
                    required=False,
                    help_text="Defaults to customer preferred currency",
                ),
                "payment_method": fields.CharField(
                    required=False,
                    help_text="Payment method code: cod, razorpay, stripe",
                ),
                "coupon_code": fields.CharField(
                    required=False,
                    help_text="Coupon code to apply a discount",
                ),
                "points_to_redeem": fields.IntegerField(
                    required=False,
                    default=0,
                    help_text="Number of loyalty points to redeem for a discount",
                ),
                "address_id": fields.UUIDField(
                    required=False,
                    help_text="UUID of an existing saved CustomerAddress",
                ),
                "new_address": inline_serializer(
                    name="NewAddressInput",
                    required=False,
                    fields={
                        "full_name": fields.CharField(),
                        "phone": fields.CharField(),
                        "address_line1": fields.CharField(),
                        "address_line2": fields.CharField(required=False),
                        "city": fields.CharField(),
                        "state": fields.CharField(),
                        "postal_code": fields.CharField(),
                        "country": fields.CharField(),
                    },
                ),
            },
        ),
        responses={201: inline_serializer(
                name="CheckoutResponse",
                fields={
                    "order_id": fields.CharField(),
                    "id": fields.UUIDField(),
                    "items": fields.ListField(),
                    "total_amount": fields.DecimalField(max_digits=12, decimal_places=2),
                    "gst": fields.DecimalField(max_digits=12, decimal_places=2),
                    "order_status": fields.CharField(),
                    "payment_status": fields.CharField(),
                },
            )},
    )
    @action(detail=True, methods=["post"])
    def checkout(self, request, pk=None):
        from apps.orders.api_v1.serializers import OrderSerializer
        order = OrderService.checkout(
            cart=self.get_object(),
            warehouse_id=request.data.get("warehouse"),
            currency=request.data.get("currency"),
            address_id=request.data.get("address_id"),
            address_data=request.data.get("new_address"),
            payment_method_code=request.data.get("payment_method"),
            coupon_code=request.data.get("coupon_code"),
            points_to_redeem=int(request.data.get("points_to_redeem", 0)),
            gift_wrap_id=request.data.get("gift_wrap_id"),
            gift_card_id=request.data.get("gift_card_id"),
        )

        # Refresh with full relations for detailed response
        from apps.orders.repositories import OrderRepository
        order = OrderRepository.list_orders().get(pk=order.pk)
        serializer = OrderSerializer(order, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    list=extend_schema(
        tags=["Cart"],
        summary="List cart items",
        parameters=[
            OpenApiParameter("cart", description="Filter by cart UUID", required=False),
            OpenApiParameter("product", description="Filter by product UUID", required=False),
            OpenApiParameter("ordering", description="Order by: created_at, quantity", required=False),
        ],
    ),
    create=extend_schema(tags=["Cart"], summary="Add a cart item"),
    retrieve=extend_schema(tags=["Cart"], summary="Get a cart item"),
    update=extend_schema(tags=["Cart"], summary="Update a cart item"),
    partial_update=extend_schema(tags=["Cart"], summary="Partially update a cart item"),
    destroy=extend_schema(tags=["Cart"], summary="Remove a cart item"),
)
class CartItemViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    queryset = CartItemRepository.list_items()
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ("cart", "product")
    ordering_fields = ("created_at", "quantity")

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_admin:
            return queryset
        return queryset.filter(cart__customer__user=self.request.user)

    @extend_schema(
        tags=["Cart"],
        summary="Buy Now - Direct Checkout (without cart)",
        description=(
            "Create an order directly from a product without adding to cart.\n\n"
            "This is for 'Buy Now' functionality - purchase immediately without cart."
        ),
        request=inline_serializer(
            name="BuyNowCheckoutRequest",
            fields={
                "product": fields.UUIDField(help_text="Product UUID"),
                "quantity": fields.IntegerField(default=1, help_text="Quantity to purchase (default: 1)"),
                "warehouse": fields.UUIDField(help_text="Warehouse UUID"),
                "color": fields.CharField(required=False, help_text="Selected color variant"),
                "size": fields.CharField(required=False, help_text="Selected size variant"),
                "currency": fields.ChoiceField(
                    choices=["INR", "GBP", "USD"],
                    required=False,
                    help_text="Currency (defaults to customer preferred)",
                ),
                "payment_method": fields.CharField(required=False, help_text="Payment method code"),
                "coupon_code": fields.CharField(required=False, help_text="Coupon code"),
                "points_to_redeem": fields.IntegerField(required=False, default=0, help_text="Points to redeem"),
                "address_id": fields.UUIDField(required=False, help_text="Shipping address ID"),
                "new_address": fields.DictField(required=False, help_text="New address data"),
            },
        ),
        responses={201: inline_serializer(
            name="BuyNowCheckoutResponse",
            fields={
                "order_id": fields.CharField(),
                "id": fields.UUIDField(),
                "total_amount": fields.DecimalField(max_digits=12, decimal_places=2),
                "gst": fields.DecimalField(max_digits=12, decimal_places=2),
                "payment_status": fields.CharField(),
            },
        )},
    )
    @action(detail=False, methods=["post"], url_path="buy-checkout")
    def buy_now_checkout(self, request):
        """Direct checkout from product - Buy Now without cart"""
        from apps.products.repositories import ProductRepository
        from apps.customers.services import CustomerService
        from decimal import Decimal

        customer = CustomerService.ensure_profile(request.user)
        
        # Validate required fields
        product_id = request.data.get("product")
        warehouse_id = request.data.get("warehouse")
        
        if not product_id:
            return Response({"error": "Product ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not warehouse_id:
            return Response({"error": "Warehouse ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get product
        product = ProductRepository.get_product_for_cart(product_id)
        if not product:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Validate quantity
        quantity = int(request.data.get("quantity", 1))
        if quantity < 1:
            return Response({"error": "Quantity must be at least 1"}, status=status.HTTP_400_BAD_REQUEST)
        if quantity > product.stock:
            return Response(
                {"error": f"Insufficient stock. Available: {product.stock}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate color/size
        selected_color = request.data.get("color", "")
        selected_size = request.data.get("size", "")
        if isinstance(selected_size, dict):
            selected_size = selected_size.get("size", "")
        elif isinstance(selected_size, str) and selected_size.startswith("{") and "size" in selected_size:
            import ast
            try:
                size_dict = ast.literal_eval(selected_size)
                if isinstance(size_dict, dict):
                    selected_size = size_dict.get("size", "")
            except Exception:
                pass
        
        if selected_color and selected_color not in product.colors:
            return Response(
                {"error": f"Invalid color '{selected_color}'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        available_sizes = [
            s.get("size") if isinstance(s, dict) else s
            for s in product.sizes
        ]
        if selected_size and selected_size not in available_sizes:
            return Response(
                {"error": f"Invalid size '{selected_size}'. Available: {available_sizes}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create a temporary cart with this product
        from apps.cart.repositories import CartRepository
        from apps.cart.services import CartService
        
        cart, _ = CartRepository.get_or_create_for_customer(customer)
        
        # Clear any existing items
        from apps.cart.models import CartItem
        CartItem.objects.filter(cart=cart).delete()
        
        # Add product to cart (will use customer's default cart)
        CartService.add_item(
            customer=customer,
            product_id=product_id,
            quantity=quantity,
            selected_color=selected_color,
            selected_size=selected_size
        )
        
        # Now checkout the cart
        try:
            order = OrderService.checkout(
                cart=cart,
                warehouse_id=warehouse_id,
                currency=request.data.get("currency"),
                address_id=request.data.get("address_id"),
                address_data=request.data.get("new_address"),
                payment_method_code=request.data.get("payment_method"),
                coupon_code=request.data.get("coupon_code"),
                points_to_redeem=int(request.data.get("points_to_redeem", 0)),
            )
            
            # Return order response
            from apps.orders.api_v1.serializers import OrderSerializer
            from apps.orders.repositories import OrderRepository
            
            order = OrderRepository.list_orders().get(pk=order.pk)
            serializer = OrderSerializer(order, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        tags=["Cart"],
        summary="Buy Now - Get order summary",
        description=(
            "Calculate order summary for immediate purchase without adding to cart.\n\n"
            "Returns subtotal, shipping, tax, and total amount for the specified product and quantity."
        ),
        request=inline_serializer(
            name="BuyNowRequest",
            fields={
                "product": fields.UUIDField(help_text="Product UUID"),
                "quantity": fields.IntegerField(default=1, help_text="Quantity to purchase (default: 1)"),
                "color": fields.CharField(required=False, help_text="Selected color variant"),
                "size": fields.CharField(required=False, help_text="Selected size variant"),
                "currency": fields.ChoiceField(
                    choices=["INR", "GBP", "USD"],
                    required=False,
                    help_text="Currency for pricing (defaults to customer preferred currency)",
                ),
            },
        ),
        responses={200: inline_serializer(
            name="BuyNowResponse",
            fields={
                "product": fields.DictField(help_text="Product details"),
                "quantity": fields.IntegerField(),
                "selected_color": fields.CharField(),
                "selected_size": fields.CharField(),
                "currency": fields.CharField(),
                "subtotal": fields.DecimalField(max_digits=12, decimal_places=2, help_text="Product price × quantity"),
                "shipping": fields.DecimalField(max_digits=12, decimal_places=2, help_text="Shipping cost"),
                "tax": fields.DecimalField(max_digits=12, decimal_places=2, help_text="Tax amount (18% GST)"),
                "total": fields.DecimalField(max_digits=12, decimal_places=2, help_text="Final total amount"),
                "total_products": fields.IntegerField(help_text="Total number of products"),
            },
        )},
    )
    @action(detail=False, methods=["post"], url_path="buy")
    def buy_now(self, request):
        from decimal import Decimal
        from apps.products.repositories import ProductRepository
        from apps.customers.services import CustomerService

        # Get customer profile
        customer = CustomerService.ensure_profile(request.user)
        
        # Get product
        product_id = request.data.get("product")
        if not product_id:
            return Response(
                {"error": "Product ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        product = ProductRepository.get_product_for_cart(product_id)
        if not product:
            return Response(
                {"error": "Product not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get quantity
        quantity = int(request.data.get("quantity", 1))
        if quantity < 1:
            return Response(
                {"error": "Quantity must be at least 1"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate stock
        if quantity > product.stock:
            return Response(
                {"error": f"Insufficient stock. Available: {product.stock}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get and validate color/size
        selected_color = request.data.get("color", "")
        selected_size = request.data.get("size", "")
        if isinstance(selected_size, dict):
            selected_size = selected_size.get("size", "")
        elif isinstance(selected_size, str) and selected_size.startswith("{") and "size" in selected_size:
            import ast
            try:
                size_dict = ast.literal_eval(selected_size)
                if isinstance(size_dict, dict):
                    selected_size = size_dict.get("size", "")
            except Exception:
                pass

        if selected_color and selected_color not in product.colors:
            return Response(
                {"error": f"Invalid color '{selected_color}'. Available: {product.colors}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        available_sizes = [
            s.get("size") if isinstance(s, dict) else s
            for s in product.sizes
        ]
        if selected_size and selected_size not in available_sizes:
            return Response(
                {"error": f"Invalid size '{selected_size}'. Available: {available_sizes}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get currency
        currency = request.data.get("currency", customer.preferred_currency)
        if currency not in ["INR", "GBP", "USD"]:
            currency = customer.preferred_currency
        
        # Calculate price based on currency
        price_map = {
            "INR": product.sale_price_inr if product.sale_price_inr is not None else product.price_inr,
            "GBP": product.sale_price_gbp if product.sale_price_gbp is not None else product.price_gbp,
            "USD": product.sale_price_usd if product.sale_price_usd is not None else product.price_usd,
        }
        unit_price = Decimal(str(price_map.get(currency) or 0))
        
        # Calculate order summary
        subtotal = (unit_price * quantity).quantize(Decimal("0.01"))
        
        # Shipping calculation (flat rate based on currency)
        shipping_rates = {
            "INR": Decimal("50.00"),
            "GBP": Decimal("5.00"),
            "USD": Decimal("7.00"),
        }
        shipping = shipping_rates.get(currency, Decimal("0.00"))
        
        # Tax calculation (18% GST)
        tax = (subtotal * Decimal("0.18")).quantize(Decimal("0.01"))
        
        # Total
        total = (subtotal + shipping + tax).quantize(Decimal("0.01"))
        
        # Get product image
        images = list(product.images.all())
        if selected_color:
            img = next((i for i in images if i.color == selected_color), None)
        else:
            img = next((i for i in images if i.is_primary), images[0] if images else None)
        
        image_url = None
        if img and img.image:
            image_url = request.build_absolute_uri(img.image.url)
        
        # Calculate variant stock to return
        variant_stock = product.stock
        if img:
            variant_stock = img.stock
            if selected_size and img.sizes:
                for size_data in img.sizes:
                    if size_data.get('size') == selected_size:
                        variant_stock = size_data.get('stock', 0)
                        break
        
        # Build response
        response_data = {
            "product": {
                "id": str(product.id),
                "name_en": product.name_en,
                "name_ar": product.name_ar,
                "sku": product.sku,
                "stock": variant_stock,
                "sizes": img.sizes if img and img.sizes else product.sizes,
                "unit_price": unit_price,
                "required_points": product.required_points,
                "image": {
                    "url": image_url,
                    "color": img.color if img else "",
                } if img else None,
            },
            "quantity": quantity,
            "selected_color": selected_color,
            "selected_size": selected_size,
            "currency": currency,
            "subtotal": subtotal,
            "shipping": shipping,
            "gst": gst,
            "total": total,
            "total_products": quantity,
            "total_required_points": product.required_points * quantity,
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
