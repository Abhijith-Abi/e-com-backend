from apps.warehouses.models import Warehouse


class WarehouseRepository:
    @staticmethod
    def list_warehouses():
        return Warehouse.objects.order_by("warehouse_name")
