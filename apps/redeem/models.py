from django.core.validators import MinValueValidator
from django.db import models

from core.base_models import BaseModel


class BillStatusChoices(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"


class TransactionTypeChoices(models.TextChoices):
    CREDIT = "credit", "Credit"       # admin adds points
    DEBIT = "debit", "Debit"          # user redeems points at checkout


class PointWallet(BaseModel):
    """One wallet per customer. Holds the current redeemable point balance."""

    customer = models.OneToOneField(
        "customers.CustomerProfile",
        on_delete=models.CASCADE,
        related_name="point_wallet",
    )
    balance = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.customer} — {self.balance} pts"


class BillUpload(BaseModel):
    """Customer uploads a purchase bill image; admin reviews and awards points."""

    customer = models.ForeignKey(
        "customers.CustomerProfile",
        on_delete=models.CASCADE,
        related_name="bill_uploads",
    )
    bill_image = models.FileField(upload_to="redeem/bills/")
    bill_number = models.CharField(max_length=100, blank=True, default="")
    bill_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Verified price/amount on the bill (optional)",
    )
    notes = models.TextField(blank=True, default="", help_text="Customer notes about the bill")
    status = models.CharField(
        max_length=16,
        choices=BillStatusChoices.choices,
        default=BillStatusChoices.PENDING,
        db_index=True,
    )
    admin_notes = models.TextField(
        blank=True,
        default="",
        help_text="Admin remarks when approving or rejecting",
    )
    points_awarded = models.PositiveIntegerField(
        default=0,
        help_text="Points manually entered by admin upon approval",
    )
    reviewed_by = models.ForeignKey(
        "user_account.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_bills",
        help_text="Admin who reviewed this bill",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    bill_code = models.CharField(
        max_length=6,
        blank=True,
        default="",
        db_index=True,
        help_text="Auto-generated 6-character hex code for this bill",
    )

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("customer", "status")),
            models.Index(fields=("status", "created_at")),
        ]

    def __str__(self):
        return f"Bill #{self.bill_number or self.id} — {self.customer} [{self.status}]"

    def save(self, *args, **kwargs):
        if not self.bill_code:
            import secrets
            self.bill_code = secrets.token_hex(3).upper()
        super().save(*args, **kwargs)

class PointTransaction(BaseModel):
    """Ledger entry for every point credit or debit on a wallet."""

    wallet = models.ForeignKey(
        "redeem.PointWallet",
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    transaction_type = models.CharField(
        max_length=8,
        choices=TransactionTypeChoices.choices,
        db_index=True,
    )
    points = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    balance_after = models.PositiveIntegerField(
        help_text="Wallet balance immediately after this transaction",
    )
    description = models.CharField(max_length=255, blank=True, default="")
    # Optional links for traceability
    bill_upload = models.ForeignKey(
        "redeem.BillUpload",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="point_transactions",
    )

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("wallet", "transaction_type")),
            models.Index(fields=("wallet", "created_at")),
        ]

    def __str__(self):
        return f"{self.transaction_type.upper()} {self.points} pts — wallet {self.wallet_id}"


class RedeemSettings(BaseModel):
    """
    Global configuration for the points/redeem system.
    Only one active row is used (singleton pattern).
    """

    points_per_currency_unit = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=1.0000,
        help_text="How many points equal 1 unit of currency (e.g. 10 pts = ₹1 → set 10)",
    )
    min_points_to_redeem = models.PositiveIntegerField(
        default=100,
        help_text="Minimum points a customer must have to redeem",
    )
    max_redeem_percent = models.PositiveIntegerField(
        default=20,
        help_text="Maximum % of order total that can be paid via points (0 = no cap)",
    )
    # is_active is inherited from BaseModel — used to enable/disable the settings row

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Redeem Settings"
        verbose_name_plural = "Redeem Settings"

    def __str__(self):
        return f"RedeemSettings (1 currency unit = {self.points_per_currency_unit} pts)"
