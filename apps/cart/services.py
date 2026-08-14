from decimal import Decimal

from apps.cart.models import CartItem
from apps.cart.repositories import CartRepository
from apps.products.repositories import ProductRepository


class CartService:
    @staticmethod
    def _price_for_currency(product, currency):
        price_map = {
            "INR": product.sale_price_inr if product.sale_price_inr is not None else product.price_inr,
            "GBP": product.sale_price_gbp if product.sale_price_gbp is not None else product.price_gbp,
            "USD": product.sale_price_usd if product.sale_price_usd is not None else product.price_usd,
        }
        return Decimal(str(price_map.get(currency) or 0))

    @classmethod
    def add_item(cls, customer, product_id, quantity, selected_color="", selected_size=""):
        # Normalize size if passed as a dictionary/object or stringified dictionary
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

        cart, _ = CartRepository.get_or_create_for_customer(customer)
        product = ProductRepository.get_product_for_cart(product_id)
        if not product:
            raise ValueError("Product not found.")
        if selected_color and selected_color not in product.colors:
            raise ValueError(f"Invalid color '{selected_color}'. Available: {product.colors}")

        available_sizes = [
            s.get("size") if isinstance(s, dict) else s
            for s in product.sizes
        ]

        if selected_size and selected_size not in available_sizes:
            raise ValueError(
                f"Invalid size '{selected_size}'. Available: {available_sizes}"
            )
        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            selected_color=selected_color,
            selected_size=selected_size,
            defaults={
                "quantity": quantity,
                "price_snapshot": cls._price_for_currency(product, customer.preferred_currency),
            },
        )
        if not created:
            item.quantity += quantity
        item.price_snapshot = cls._price_for_currency(product, customer.preferred_currency)
        item.save(update_fields=["quantity", "price_snapshot", "updated_at"])
        return item
