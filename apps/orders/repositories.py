from apps.orders.models import Order, OrderItem


class OrderRepository:
    @staticmethod
    def list_orders():
        return (
            Order.objects.select_related("customer__user", "warehouse", "courier", "shipping_address")
            .prefetch_related("items__product", "status_history", "payment_history")
            .order_by("-created_at")
        )


class OrderItemRepository:
    @staticmethod
    def list_items():
        return OrderItem.objects.select_related("order", "product").order_by("created_at")
