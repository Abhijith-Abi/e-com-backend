from apps.redeem.models import BillUpload, BillStatusChoices, PointTransaction, PointWallet, RedeemSettings


class PointWalletRepository:
    @staticmethod
    def get_or_create_for_customer(customer):
        wallet, _ = PointWallet.objects.get_or_create(customer=customer)
        return wallet

    @staticmethod
    def get_for_customer(customer):
        return PointWallet.objects.filter(customer=customer).first()


class BillUploadRepository:
    @staticmethod
    def list_all():
        return BillUpload.objects.select_related("customer__user", "reviewed_by").order_by("-created_at")

    @staticmethod
    def list_pending():
        return (
            BillUpload.objects.select_related("customer__user", "reviewed_by")
            .filter(status=BillStatusChoices.PENDING)
            .order_by("-created_at")
        )

    @staticmethod
    def list_for_customer(customer):
        return BillUpload.objects.filter(customer=customer).order_by("-created_at")

    @staticmethod
    def get_by_id(bill_id):
        return BillUpload.objects.select_related("customer__user", "reviewed_by").filter(id=bill_id).first()


class PointTransactionRepository:
    @staticmethod
    def list_for_wallet(wallet):
        return PointTransaction.objects.filter(wallet=wallet).prefetch_related("order__items__product").order_by("-created_at")

    @staticmethod
    def list_all():
        return PointTransaction.objects.select_related("wallet__customer__user").prefetch_related("order__items__product").order_by("-created_at")


class RedeemSettingsRepository:
    @staticmethod
    def get_active():
        return RedeemSettings.objects.filter(is_active=True).order_by("-created_at").first()
