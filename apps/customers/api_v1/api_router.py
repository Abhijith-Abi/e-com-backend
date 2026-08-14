from django.urls import path
from rest_framework.routers import SimpleRouter

from apps.customers.api_v1.views import CustomerAddressViewSet, CustomerProfileViewSet, MyAddressViewSet, WishlistViewSet

app_name = "customers_api_v1"

router = SimpleRouter()
router.register("profiles", CustomerProfileViewSet, basename="customer-profiles")
router.register("wishlists", WishlistViewSet, basename="wishlists")
router.register("addresses", MyAddressViewSet, basename="my-addresses")

urlpatterns = router.urls + [
    path(
        "profiles/<uuid:customer_id>/addresses/",
        CustomerAddressViewSet.as_view({"get": "list", "post": "create"}),
        name="customer-addresses-list",
    ),
    path(
        "profiles/<uuid:customer_id>/addresses/<uuid:pk>/",
        CustomerAddressViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}),
        name="customer-addresses-detail",
    ),
]
