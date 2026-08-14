from django.utils import timezone

from apps.coupons.models import Coupon, CouponUsage, Offer
from core.choices import StatusChoices


class CouponRepository:
    @staticmethod
    def list_coupons():
        from django.db.models import Count, Q
        from core.choices import OrderStatusChoices
        return (
            Coupon.objects.annotate(
                actual_usage=Count(
                    "orders",
                    filter=~Q(orders__order_status=OrderStatusChoices.CANCELLED),
                )
            )
            .order_by("-created_at")
        )

    @staticmethod
    def get_valid_coupon(code, region, customer=None):
        """
        Validates a coupon for use.
        
        Args:
            code: The coupon code to validate
            region: The region where the coupon should be valid
            customer: The CustomerProfile instance (optional, but required for per-user validation)
        
        Returns:
            Coupon instance if valid, None otherwise
        """
        now = timezone.now()
        from django.utils.timezone import make_aware
        from datetime import datetime, time
        # Extend valid_until to end of day (23:59:59) so coupon works on the expiry date
        end_of_today = make_aware(datetime.combine(now.date(), time(23, 59, 59)))
        effective_now = min(now, end_of_today)
        coupon = Coupon.objects.filter(
            coupon_code=code,
            region=region,
            status=StatusChoices.ACTIVE,
            valid_from__lte=now,
            valid_until__date__gte=now.date(),
        ).first()

        if not coupon:
            return None

        # Ensure exact case match (databases like MySQL are often case-insensitive by default)
        if coupon.coupon_code != code:
            return None

        # Check if customer has already used this coupon
        if customer:
            has_used = CouponUsage.objects.filter(
                coupon=coupon,
                customer=customer
            ).exists()
            if has_used:
                return None

        # Check global usage limit
        if coupon.usage_limit is not None:
            from core.choices import OrderStatusChoices
            usage_count = coupon.orders.exclude(order_status=OrderStatusChoices.CANCELLED).count()
            if usage_count >= coupon.usage_limit:
                return None
        
        return coupon

    @staticmethod
    def record_coupon_usage(coupon, customer, order):
        """
        Records that a customer has used a coupon for an order.
        
        Args:
            coupon: Coupon instance
            customer: CustomerProfile instance
            order: Order instance
        
        Returns:
            CouponUsage instance
        """
        usage, created = CouponUsage.objects.get_or_create(
            coupon=coupon,
            customer=customer,
            defaults={"order": order}
        )
        return usage


class OfferRepository:
    @staticmethod
    def list_offers():
        return Offer.objects.select_related("warehouse").order_by("-created_at")

    @staticmethod
    def list_offers_by_warehouse(warehouse_id):
        return (
            Offer.objects.select_related("warehouse")
            .filter(warehouse_id=warehouse_id)
            .order_by("-created_at")
        )
