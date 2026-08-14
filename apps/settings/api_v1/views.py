from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.settings.api_v1.serializers import CurrencySettingsSerializer, ShippingSettingsSerializer, StoreSettingsSerializer
from apps.settings.repositories import CurrencySettingsRepository, ShippingSettingsRepository, StoreSettingsRepository
from core.permissions import IsAdminOrReadOnly, IsWarehouseAdminOrAdmin


class StoreSettingsSingletonView(APIView):
    """
    Global store settings — singleton.
    GET  → return the single record (or 404)
    POST → create if none exists, otherwise update (upsert)
    PATCH → partial update existing record
    """
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = StoreSettingsSerializer

    def _get_instance(self):
        return StoreSettingsRepository.get_global()

    def _get_warehouse(self):
        return None

    @extend_schema(tags=["Settings"], summary="Get store settings")
    def get(self, request, *args, **kwargs):
        instance = self._get_instance()
        if not instance:
            return Response({"detail": "Store settings not configured yet."}, status=status.HTTP_404_NOT_FOUND)
        return Response(StoreSettingsSerializer(instance).data)

    @extend_schema(tags=["Settings"], summary="Create or update store settings")
    def post(self, request, *args, **kwargs):
        instance = self._get_instance()
        if instance:
            # Already exists — update instead
            serializer = StoreSettingsSerializer(instance, data=request.data, partial=False)
        else:
            serializer = StoreSettingsSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        obj = serializer.save(warehouse=self._get_warehouse())
        code = status.HTTP_200_OK if instance else status.HTTP_201_CREATED
        return Response(StoreSettingsSerializer(obj).data, status=code)

    @extend_schema(tags=["Settings"], summary="Partially update store settings")
    def patch(self, request, *args, **kwargs):
        instance = self._get_instance()
        if not instance:
            return Response({"detail": "Store settings not configured yet."}, status=status.HTTP_404_NOT_FOUND)
        serializer = StoreSettingsSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(StoreSettingsSerializer(obj).data)


class WarehouseStoreSettingsSingletonView(StoreSettingsSingletonView):
    """
    Warehouse-scoped store settings — singleton per warehouse.
    GET  → return the record (or 404)
    POST → create if none exists, otherwise update (upsert)
    """
    permission_classes = [IsWarehouseAdminOrAdmin]
    http_method_names = ["get", "post", "head", "options"]

    def _get_instance(self):
        wh = getattr(self.request, "warehouse", None)
        if not wh:
            return None
        return StoreSettingsRepository.get_by_warehouse(wh.id)

    def _get_warehouse(self):
        return getattr(self.request, "warehouse", None)

    @extend_schema(tags=["Warehouse Settings"], summary="Get warehouse store settings")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(tags=["Warehouse Settings"], summary="Create or update warehouse store settings")
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


@extend_schema_view(
    list=extend_schema(tags=["Settings"], summary="List currency settings"),
    create=extend_schema(tags=["Settings"], summary="Create currency settings"),
    retrieve=extend_schema(tags=["Settings"], summary="Get currency settings"),
    update=extend_schema(tags=["Settings"], summary="Update currency settings"),
    partial_update=extend_schema(tags=["Settings"], summary="Partially update currency settings"),
    destroy=extend_schema(tags=["Settings"], summary="Delete currency settings"),
)
class CurrencySettingsViewSet(viewsets.ModelViewSet):
    serializer_class = CurrencySettingsSerializer
    queryset = CurrencySettingsRepository.list_currency_settings()
    permission_classes = [IsAdminOrReadOnly]


@extend_schema_view(
    list=extend_schema(tags=["Settings"], summary="List shipping settings"),
    create=extend_schema(tags=["Settings"], summary="Create shipping settings"),
    retrieve=extend_schema(tags=["Settings"], summary="Get shipping settings"),
    update=extend_schema(tags=["Settings"], summary="Update shipping settings"),
    partial_update=extend_schema(tags=["Settings"], summary="Partially update shipping settings"),
    destroy=extend_schema(tags=["Settings"], summary="Delete shipping settings"),
)
class ShippingSettingsViewSet(viewsets.ModelViewSet):
    serializer_class = ShippingSettingsSerializer
    queryset = ShippingSettingsRepository.list_shipping_settings()
    permission_classes = [IsAdminOrReadOnly]
