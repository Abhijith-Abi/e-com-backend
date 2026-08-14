from django.urls import path
from rest_framework.routers import SimpleRouter

from apps.redeem.api_v1.views import (
    AdminBillUploadViewSet,
    AdminPointTransactionViewSet,
    MyBillUploadView,
    MyTransactionListView,
    MyWalletView,
    PointWalletViewSet,
    ProductRedeemView,
    RedeemPointsApplyView,
    RedeemPointsCheckView,
    RedeemSettingsViewSet,
)

app_name = "redeem_api_v1"

router = SimpleRouter()
router.register("admin/wallets", PointWalletViewSet, basename="admin-wallets")
router.register("admin/bills", AdminBillUploadViewSet, basename="admin-bills")
router.register("admin/transactions", AdminPointTransactionViewSet, basename="admin-transactions")
router.register("settings", RedeemSettingsViewSet, basename="redeem-settings")

urlpatterns = router.urls + [
    # ── Customer: wallet & history ──────────────────────────────────────────
    path("wallet/", MyWalletView.as_view(), name="my-wallet"),
    path("bills/", MyBillUploadView.as_view(), name="my-bills"),
    path("transactions/", MyTransactionListView.as_view(), name="my-transactions"),

    # ── Checkout helpers ────────────────────────────────────────────────────
    # 1. Dry-run: preview discount before checkout
    path("check/", RedeemPointsCheckView.as_view(), name="redeem-check"),
    # 2. Apply points to an already-created order
    path("apply/<uuid:order_id>/", RedeemPointsApplyView.as_view(), name="redeem-apply"),

    # ── Product redeem (points-only purchase) ───────────────────────────────
    path("product/", ProductRedeemView.as_view(), name="product-redeem"),

]
