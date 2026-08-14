from apps.payments.models import Payment
from core.choices import PaymentStatusChoices


class PaymentService:
    @staticmethod
    def mark_paid(payment, transaction_id):
        payment.payment_status = PaymentStatusChoices.PAID
        payment.transaction_id = transaction_id
        payment.save(update_fields=["payment_status", "transaction_id", "updated_at"])
        order = payment.order
        order.payment_status = payment.payment_status
        order.save(update_fields=["payment_status", "updated_at"])
        return payment
