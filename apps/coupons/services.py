from decimal import Decimal

from core.choices import CouponTypeChoices


class CouponService:
    @staticmethod
    def apply_discount(coupon, amount):
        amount = Decimal(amount)
        if coupon.coupon_type == CouponTypeChoices.PERCENTAGE:
            discount = amount * (coupon.coupon_value / Decimal("100"))
            return max(amount - discount, Decimal("0.00"))
        return max(amount - coupon.coupon_value, Decimal("0.00"))
