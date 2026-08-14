from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.redeem.models import BillStatusChoices, PointTransaction, TransactionTypeChoices
from apps.redeem.repositories import BillUploadRepository, PointWalletRepository, RedeemSettingsRepository


class PointWalletService:
    @staticmethod
    def get_or_create(customer):
        return PointWalletRepository.get_or_create_for_customer(customer)

    @classmethod
    @transaction.atomic
    def credit_points(cls, customer, points: int, description: str = "", bill_upload=None, order=None):
        """Add points to a customer's wallet. Returns the updated wallet."""
        if points <= 0:
            raise ValueError("Points to credit must be a positive integer.")
        wallet = PointWalletRepository.get_or_create_for_customer(customer)
        wallet.balance += points
        wallet.save(update_fields=["balance", "updated_at"])
        PointTransaction.objects.create(
            wallet=wallet,
            transaction_type=TransactionTypeChoices.CREDIT,
            points=points,
            balance_after=wallet.balance,
            description=description or f"Points credited",
            bill_upload=bill_upload,
            order=order,
        )
        return wallet

    @classmethod
    @transaction.atomic
    def debit_points(cls, customer, points: int, description: str = "", order=None):
        """Deduct points from a customer's wallet. Returns the updated wallet."""
        if points <= 0:
            raise ValueError("Points to debit must be a positive integer.")
        wallet = PointWalletRepository.get_or_create_for_customer(customer)
        if wallet.balance < points:
            raise ValueError(f"Insufficient points. Available: {wallet.balance}, requested: {points}.")
        wallet.balance -= points
        wallet.save(update_fields=["balance", "updated_at"])
        PointTransaction.objects.create(
            wallet=wallet,
            transaction_type=TransactionTypeChoices.DEBIT,
            points=points,
            balance_after=wallet.balance,
            description=description or "Points redeemed at checkout",
            order=order,
        )
        return wallet

    @staticmethod
    def points_to_currency(points: int, settings=None) -> Decimal:
        """Convert points to currency value based on active settings."""
        if settings is None:
            settings = RedeemSettingsRepository.get_active()
        if not settings:
            return Decimal("0.00")
        return (Decimal(points) / Decimal(str(settings.points_per_currency_unit))).quantize(Decimal("0.01"))

    @staticmethod
    def currency_to_points(amount: Decimal, settings=None) -> int:
        """Convert a currency amount to equivalent points."""
        if settings is None:
            settings = RedeemSettingsRepository.get_active()
        if not settings:
            return 0
        return int(Decimal(str(amount)) * Decimal(str(settings.points_per_currency_unit)))

    @staticmethod
    def validate_redemption(customer, points_to_redeem: int, total_required_points: int, settings=None):
        """
        Validate and allow partial point redemption.
        User can redeem up to min(available_points, required_points).
        Returns (is_valid, error_message, points_discount_amount, points_actually_redeemed).
        """
        if settings is None:
            settings = RedeemSettingsRepository.get_active()
        if not settings:
            return False, "Redeem system is not configured.", Decimal("0.00"), 0

        wallet = PointWalletRepository.get_or_create_for_customer(customer)
        
        # User cannot redeem more points than they have
        if points_to_redeem > wallet.balance:
            return False, f"You only have {wallet.balance} points available.", Decimal("0.00"), 0
        
        # User cannot redeem more points than required
        if points_to_redeem > total_required_points:
            return False, f"This order only requires {total_required_points} points maximum.", Decimal("0.00"), 0
        
        # Points to actually redeem (user's choice, but not more than available or required)
        points_actually_redeemed = min(int(points_to_redeem), wallet.balance, total_required_points)
        
        # Convert redeemed points to currency discount
        discount = PointWalletService.points_to_currency(points_actually_redeemed, settings)
        
        return True, None, discount, points_actually_redeemed

class BillUploadService:
    @classmethod
    @transaction.atomic
    def approve_bill(cls, bill, admin_user, bill_price: Decimal, admin_notes: str = ""):
        """Admin approves a bill, sets bill_price, and automatically awards points (1% of bill_price)."""
        if bill.status != BillStatusChoices.PENDING:
            raise ValueError("Only pending bills can be approved.")
        if bill_price <= 0:
            raise ValueError("Bill price must be greater than zero.")

        points = int(bill_price * Decimal("0.01"))
        if points <= 0:
            raise ValueError("Bill price is too small to award any points.")

        bill.status = BillStatusChoices.APPROVED
        bill.bill_price = bill_price
        bill.points_awarded = points
        bill.admin_notes = admin_notes
        bill.reviewed_by = admin_user
        bill.reviewed_at = timezone.now()
        bill.save(update_fields=["status", "bill_price", "points_awarded", "admin_notes", "reviewed_by", "reviewed_at", "updated_at"])

        PointWalletService.credit_points(
            customer=bill.customer,
            points=points,
            description=f"Points awarded for bill #{bill.bill_number or bill.id}",
            bill_upload=bill,
        )
        return bill

    @classmethod
    @transaction.atomic
    def reject_bill(cls, bill, admin_user, admin_notes: str = ""):
        """Admin rejects a bill without awarding points."""
        if bill.status != BillStatusChoices.PENDING:
            raise ValueError("Only pending bills can be rejected.")

        bill.status = BillStatusChoices.REJECTED
        bill.admin_notes = admin_notes
        bill.reviewed_by = admin_user
        bill.reviewed_at = timezone.now()
        bill.save(update_fields=["status", "admin_notes", "reviewed_by", "reviewed_at", "updated_at"])
        return bill
