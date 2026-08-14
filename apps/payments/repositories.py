from apps.payments.models import Payment


class PaymentRepository:
    @staticmethod
    def list_payments():
        return Payment.objects.select_related("order", "order__customer__user").order_by("-created_at")
