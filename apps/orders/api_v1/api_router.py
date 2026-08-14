from django.urls import path
from rest_framework.routers import SimpleRouter
from apps.orders.api_v1.views import OrderInvoiceView, CustomerOrderItemsView
from apps.orders.api_v1.views import OrderItemViewSet, OrderViewSet, OrderTrackingView

app_name = "orders_api_v1"

router = SimpleRouter()
router.register("records", OrderViewSet, basename="orders")
router.register("items", OrderItemViewSet, basename="order-items")

urlpatterns = router.urls + [
    path("track/", OrderTrackingView.as_view(), name="order-tracking"),
    path("customer/<uuid:customer_id>/items/", CustomerOrderItemsView.as_view(), name="customer-order-items"),
    path("records/<uuid:order_id>/invoice/", OrderInvoiceView.as_view(), name="order-invoice"),
]
