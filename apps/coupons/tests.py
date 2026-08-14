from datetime import timedelta
from decimal import Decimal
from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.coupons.models import Coupon
from apps.coupons.repositories import CouponRepository
from apps.orders.models import Order
from apps.customers.models import CustomerProfile
from apps.warehouses.models import Warehouse
from core.choices import CouponTypeChoices, RegionChoices, StatusChoices, OrderStatusChoices

User = get_user_model()

class CouponUsageLimitTestCase(TransactionTestCase):
    def setUp(self):
        # Create a test user and profile
        self.user = User.objects.create_user(
            email="customer@example.com",
            password="password123",
            full_name="John Doe"
        )
        self.customer = CustomerProfile.objects.create(
            user=self.user,
            preferred_currency="USD",
        )
        # Create a warehouse
        self.warehouse = Warehouse.objects.create(
            warehouse_name="Test Warehouse",
            is_active=True
        )

        now = timezone.now()
        # Create a coupon with usage limit of 2
        self.coupon = Coupon.objects.create(
            coupon_code="LIMIT2",
            coupon_type=CouponTypeChoices.PERCENTAGE,
            coupon_value=Decimal("10.00"),
            valid_from=now - timedelta(days=1),
            valid_until=now + timedelta(days=1),
            usage_limit=2,
            region=RegionChoices.INDIA,
            status=StatusChoices.ACTIVE
        )

    def test_coupon_valid_within_limit(self):
        # Initial check should be valid since usage_count is 0
        valid_coupon = CouponRepository.get_valid_coupon("LIMIT2", RegionChoices.INDIA)
        self.assertIsNotNone(valid_coupon)

        # Create one order using this coupon
        Order.objects.create(
            order_id="ORD-1",
            customer=self.customer,
            warehouse=self.warehouse,
            currency="USD",
            applied_coupon=self.coupon,
            total_amount=Decimal("100.00"),
            order_status=OrderStatusChoices.CONFIRMED
        )

        # Should still be valid since usage_count (1) is less than usage_limit (2)
        valid_coupon = CouponRepository.get_valid_coupon("LIMIT2", RegionChoices.INDIA)
        self.assertIsNotNone(valid_coupon)

        # Create second order using this coupon
        order2 = Order.objects.create(
            order_id="ORD-2",
            customer=self.customer,
            warehouse=self.warehouse,
            currency="USD",
            applied_coupon=self.coupon,
            total_amount=Decimal("100.00"),
            order_status=OrderStatusChoices.CONFIRMED
        )

        # Should now be invalid since usage_count (2) has reached usage_limit (2)
        valid_coupon = CouponRepository.get_valid_coupon("LIMIT2", RegionChoices.INDIA)
        self.assertIsNone(valid_coupon)

        # If one of the orders gets cancelled, the coupon should become valid again!
        order2.order_status = OrderStatusChoices.CANCELLED
        order2.save()

        valid_coupon = CouponRepository.get_valid_coupon("LIMIT2", RegionChoices.INDIA)
        self.assertIsNotNone(valid_coupon)

    def test_coupon_valid_until_midnight_adjusted(self):
        # Create a coupon with valid_until set to midnight (00:00:00)
        from datetime import datetime
        now = timezone.now()
        target_date = datetime(2026, 5, 7, 0, 0, 0, tzinfo=timezone.get_current_timezone())
        coupon = Coupon.objects.create(
            coupon_code="MIDNIGHT_TEST",
            coupon_type=CouponTypeChoices.PERCENTAGE,
            coupon_value=Decimal("10.00"),
            valid_from=now - timedelta(days=1),
            valid_until=target_date,
            region=RegionChoices.INDIA,
            status=StatusChoices.ACTIVE
        )

        # After saving, the valid_until should be adjusted to 23:59:59 of that day
        self.assertEqual(coupon.valid_until.hour, 23)
        self.assertEqual(coupon.valid_until.minute, 59)
        self.assertEqual(coupon.valid_until.second, 59)
