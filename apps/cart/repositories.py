from apps.cart.models import Cart, CartItem


class CartRepository:
    @staticmethod
    def list_carts():
        return Cart.objects.select_related("customer__user").prefetch_related(
            "items__product__images"
        ).order_by("-updated_at")

    @staticmethod
    def get_or_create_for_customer(customer):
        return Cart.objects.get_or_create(customer=customer)


class CartItemRepository:
    @staticmethod
    def list_items():
        return CartItem.objects.select_related("cart__customer__user", "product").prefetch_related(
            "product__images"
        ).order_by("-created_at")
