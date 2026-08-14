from apps.customers.models import CustomerAddress, CustomerProfile, Wishlist


class CustomerRepository:
    @staticmethod
    def list_profiles():
        return CustomerProfile.objects.select_related("user").order_by("-created_at")

    @staticmethod
    def list_profiles_with_orders_and_addresses():
        return (
            CustomerProfile.objects.select_related("user")
            .prefetch_related(
                "orders__items__product",
                "addresses",
            )
            .order_by("-created_at")
        )


class CustomerAddressRepository:
    @staticmethod
    def list_addresses(customer_id=None):
        qs = CustomerAddress.objects.all()
        if customer_id:
            qs = qs.filter(customer_id=customer_id)
        return qs


class WishlistRepository:
    @staticmethod
    def list_wishlists():
        return Wishlist.objects.select_related("customer__user", "product", "product__category").prefetch_related(
            "product__images"
        ).order_by("-created_at")
