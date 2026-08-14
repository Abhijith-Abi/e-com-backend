from django.db.models import ProtectedError
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.categories.api_v1.serializers import CategorySerializer, CategoryChildSerializer, CategoryTreeSerializer
from apps.categories.repositories import CategoryRepository
from core.pagination import CustomPageNumberPagination
from core.permissions import IsAdminOrReadOnly, IsWarehouseAdminOrAdmin


@extend_schema_view(
    list=extend_schema(
        tags=["Categories"],
        summary="List all categories",
        parameters=[
            OpenApiParameter("status", description="Filter by status (active, inactive)", required=False),
            OpenApiParameter("parent", description="Filter by parent category UUID", required=False),
            OpenApiParameter("is_major", description="Filter major categories (true/false)", required=False),
            OpenApiParameter("search", description="Search by name_en, name_ar, slug", required=False),
            OpenApiParameter("ordering", description="Order by: name_en, created_at", required=False),
        ],
    ),
    create=extend_schema(tags=["Categories"], summary="Create a category"),
    retrieve=extend_schema(tags=["Categories"], summary="Get a category"),
    update=extend_schema(tags=["Categories"], summary="Update a category"),
    partial_update=extend_schema(tags=["Categories"], summary="Partially update a category"),
    destroy=extend_schema(tags=["Categories"], summary="Delete a category"),
)

class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    pagination_class = None
    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAdminOrReadOnly()]
    queryset = CategoryRepository.list_categories()
    filterset_fields = ("status", "parent", "is_major", "warehouse")
    search_fields = ("name_en", "name_ar", "slug", "sub_heading", "sub_heading_ar")
    ordering_fields = ("name_en", "created_at", "latest_activity")
    ordering = ("-latest_activity", "is_child", "-created_at")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            instance.delete()
        except ProtectedError:
            return Response(
                {"detail": "Cannot delete this category because it has sub-categories or products linked to it."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    list=extend_schema(
        tags=["Warehouse Categories"],
        summary="List categories for a specific warehouse",
        parameters=[
            OpenApiParameter("status", description="Filter by status", required=False),
            OpenApiParameter("parent", description="Filter by parent UUID", required=False),
            OpenApiParameter("is_major", description="Filter major categories (true/false)", required=False),
            OpenApiParameter("search", description="Search by name_en, name_ar", required=False),
        ],
    ),
    create=extend_schema(tags=["Warehouse Categories"], summary="Create a category in this warehouse"),
    retrieve=extend_schema(tags=["Warehouse Categories"], summary="Get a category"),
    update=extend_schema(tags=["Warehouse Categories"], summary="Update a category"),
    partial_update=extend_schema(tags=["Warehouse Categories"], summary="Partially update a category"),
    destroy=extend_schema(tags=["Warehouse Categories"], summary="Delete a category"),
)

class WarehouseScopedCategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    pagination_class = None
    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsWarehouseAdminOrAdmin()]
    filterset_fields = ("status", "parent", "is_major")
    search_fields = ("name_en", "name_ar", "slug", "sub_heading", "sub_heading_ar")
    ordering_fields = ("name_en", "created_at", "latest_activity")
    ordering = ("-latest_activity", "is_child", "-created_at")

    def get_queryset(self):
        if not hasattr(self.request, "warehouse") or not self.request.warehouse:
            return CategoryRepository.list_categories().none()
        return CategoryRepository.list_categories_by_warehouse(self.request.warehouse.id)

    def perform_create(self, serializer):
        serializer.save(warehouse=self.request.warehouse)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            instance.delete()
        except ProtectedError:
            return Response(
                {"detail": "Cannot delete this category because it has sub-categories or products linked to it."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=["Warehouse Categories"],
    summary="List parent categories with their children (tree view)",
    parameters=[
        OpenApiParameter("page", description="Page number", required=False, type=int),
        OpenApiParameter("page_size", description="Number of parent categories per page (default 10)", required=False, type=int),
        OpenApiParameter("status", description="Filter by status (active, inactive)", required=False),
        OpenApiParameter("search", description="Search by parent or child name_en/name_ar", required=False),
    ],
)
class WarehouseCategoryTreeView(ListAPIView):
    serializer_class = CategoryTreeSerializer
    permission_classes = [AllowAny]
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        from django.db.models import Q
        warehouse = getattr(self.request, "warehouse", None)
        if not warehouse:
            return CategoryRepository.list_categories().none()

        qs = CategoryRepository.list_categories_by_warehouse(warehouse.id).filter(parent=None).order_by("-latest_activity")

        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(name_en__icontains=search) |
                Q(name_ar__icontains=search) |
                Q(children__name_en__icontains=search) |
                Q(children__name_ar__icontains=search)
            ).distinct()

        return qs.prefetch_related("children")

    def list(self, request, *args, **kwargs):
        from django.db.models import Q
        import math

        warehouse = getattr(request, "warehouse", None)
        if not warehouse:
            return Response({"count": 0, "next": None, "previous": None, "results": []})

        search = request.query_params.get("search")
        status_filter = request.query_params.get("status")

        # Get all parent categories for this warehouse with annotations for correct product counts
        from apps.categories.models import Category
        from django.db.models import Count

        parents_qs = (
            CategoryRepository.list_categories_by_warehouse(warehouse.id)
            .filter(parent=None)
            .order_by("-latest_activity")
        )
        if status_filter:
            parents_qs = parents_qs.filter(status=status_filter)
        if search:
            # Find parents that match OR parents that have matching children
            matching_child_parent_ids = Category.objects.filter(
                warehouse=warehouse,
                parent__isnull=False,
            ).filter(
                Q(name_en__icontains=search) | Q(name_ar__icontains=search)
            ).values_list("parent_id", flat=True)

            parents_qs = parents_qs.filter(
                Q(name_en__icontains=search) |
                Q(name_ar__icontains=search) |
                Q(id__in=matching_child_parent_ids)
            )


        # Build flat list: for each parent, add parent then its children
        flat_list = []
        for parent in parents_qs:
            flat_list.append({"type": "parent", "obj": parent})
            # Refetch children WITH annotations so product counts are correct
            children = (
                CategoryRepository.list_categories_by_warehouse(warehouse.id)
                .filter(parent_id=parent.id)
                .order_by("-created_at")
            )
            if search:
                children = children.filter(
                    Q(name_en__icontains=search) | Q(name_ar__icontains=search)
                )
            for child in children:
                flat_list.append({"type": "child", "obj": child})

        # Paginate by parent groups — allow natural split across pages
        page_size = int(request.query_params.get("page_size") or 10)
        page_num = int(request.query_params.get("page") or 1)

        # Simple slice pagination - no parent prepending
        total = len(flat_list)
        start = (page_num - 1) * page_size
        end = start + page_size
        page_items = flat_list[start:end]

        total_pages = math.ceil(total / page_size) if total > 0 else 1
        base_url = request.build_absolute_uri(request.path)

        def make_url(p):
            return "{}?page={}&page_size={}".format(base_url, p, page_size)

        # Build nested results — group children back under their parent
        results = []
        current_parent_data = None
        for item in page_items:
            obj = item["obj"]
            data = CategoryTreeSerializer(obj, context={"request": request}).data
            if item["type"] == "parent":
                if current_parent_data is not None:
                    results.append(current_parent_data)
                data["children"] = []
                data["is_parent"] = True
                current_parent_data = data
            else:
                data["is_parent"] = False
                if current_parent_data is not None:
                    current_parent_data["children"].append(data)
                else:
                    results.append(data)

        if current_parent_data is not None:
            results.append(current_parent_data)


        return Response({
            "count": total,
            "total_pages": total_pages,
            "current_page": page_num,
            "page_size": page_size,
            "next": make_url(page_num + 1) if page_num < total_pages else None,
            "previous": make_url(page_num - 1) if page_num > 1 else None,
            "results": results
        })


@extend_schema(
    tags=["Warehouse Categories"],
    summary="List subcategories (children) of a parent category",
    parameters=[
        OpenApiParameter("parent", description="Parent category UUID", required=True),
    ],
)
class WarehouseCategoryChildrenView(ListAPIView):
    permission_classes = [AllowAny]
    pagination_class = None

    def get(self, request, *args, **kwargs):
        parent_id = request.query_params.get("parent")
        warehouse = getattr(request, "warehouse", None)
        if not parent_id or not warehouse:
            return Response([])

        from apps.categories.models import Category
        children = Category.objects.filter(
            warehouse=warehouse,
            parent_id=parent_id,
            status="active",
            is_deleted=False
        ).values("id", "name_en", "name_ar", "slug").order_by("-created_at")

        return Response(list(children))
