import re

from django.http import JsonResponse

from apps.warehouses.models import Warehouse

# Matches /api/v1/warehouses/<uuid>/...
WAREHOUSE_SCOPED_PATTERN = re.compile(
    r"^/api/v1/warehouses/(?P<warehouse_id>[0-9a-f-]+)/"
)


class WarehouseScopingMiddleware:
    """
    Intercepts requests matching /api/v1/warehouses/<warehouse_id>/products/*
    Validates the warehouse exists and is active, then attaches it to request.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        match = WAREHOUSE_SCOPED_PATTERN.match(request.path)
        if match:
            warehouse_id = match.group("warehouse_id")
            warehouse = (
                Warehouse.objects.filter(id=warehouse_id, is_active=True, is_deleted=False)
                .first()
            )
            if not warehouse:
                return JsonResponse(
                    {"detail": "Warehouse not found or inactive."}, status=404
                )
            request.warehouse = warehouse
        else:
            request.warehouse = None

        return self.get_response(request)
