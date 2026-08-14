from rest_framework.routers import SimpleRouter

from apps.customers.api_v1.views import WarehouseScopedCustomerProfileViewSet

app_name = "warehouse_customers_api_v1"

router = SimpleRouter()
router.register("profiles", WarehouseScopedCustomerProfileViewSet, basename="warehouse-customer-profiles")

urlpatterns = router.urls
