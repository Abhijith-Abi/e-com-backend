from apps.couriers.models import Courier


class CourierRepository:
    @staticmethod
    def list_couriers():
        return Courier.objects.select_related("warehouse").order_by("-created_at")
