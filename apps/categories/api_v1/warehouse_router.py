from django.urls import path
from rest_framework.routers import SimpleRouter

from apps.categories.api_v1.views import WarehouseScopedCategoryViewSet, WarehouseCategoryTreeView, WarehouseCategoryChildrenView


app_name = "warehouse_categories_api_v1"

router = SimpleRouter()
router.register("", WarehouseScopedCategoryViewSet, basename="warehouse-categories")

urlpatterns = [
    path("tree/", WarehouseCategoryTreeView.as_view(), name="warehouse-categories-tree"),
    path("children/", WarehouseCategoryChildrenView.as_view(), name="warehouse-category-children"),

] + router.urls
