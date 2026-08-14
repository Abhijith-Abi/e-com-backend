from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from django.core import mail
from apps.orders.models import Order
from apps.customers.models import CustomerProfile
from apps.warehouses.models import Warehouse
from core.choices import OrderStatusChoices

User = get_user_model()

class OrderConfirmationEmailTestCase(TransactionTestCase):
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

    def test_email_sent_on_order_confirmed(self):
        # Clear outbox
        mail.outbox = []

        # Create order in pending status
        order = Order.objects.create(
            order_id="ORD-TEST-12345",
            customer=self.customer,
            warehouse=self.warehouse,
            currency="USD",
            total_amount=100.00,
            order_status=OrderStatusChoices.PENDING
        )

        # No email should be sent for pending order
        self.assertEqual(len(mail.outbox), 0)

        # Update order status to confirmed
        order.order_status = OrderStatusChoices.CONFIRMED
        order.save()

        # Email should be sent
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        self.assertIn("customer@example.com", sent_email.to)
        self.assertEqual(sent_email.subject, "Order Confirmed: ORD-TEST-12345")
        self.assertIn("Order Confirmed", sent_email.subject)


class OrderTokenCheckoutTestCase(TransactionTestCase):
    def setUp(self):
        from decimal import Decimal
        from apps.cart.models import Cart, CartItem
        from apps.products.models import Product
        from apps.categories.models import Category
        from apps.redeem.models import PointWallet
        from apps.payments.models import PaymentMethod
        from apps.redeem.repositories import PointWalletRepository
        from core.choices import PaymentMethodChoices

        # Create test user and customer profile
        self.user = User.objects.create_user(
            email="token-customer@example.com",
            password="password123",
            full_name="Token Customer"
        )
        self.customer = CustomerProfile.objects.create(
            user=self.user,
            preferred_currency="INR",
        )
        # Create a warehouse
        self.warehouse = Warehouse.objects.create(
            warehouse_name="Main Warehouse",
            is_active=True
        )
        # Create a category
        self.category = Category.objects.create(
            name_en="Electronics",
            status="active"
        )
        # Create a product that requires points (tokens)
        self.product = Product.objects.create(
            warehouse=self.warehouse,
            name_en="Token Product",
            sku="TOKEN-SKU-123",
            category=self.category,
            price_inr=Decimal("500.00"),
            stock=10,
            status="active",
            required_points=100  # Requires 100 tokens
        )
        # Create a payment method
        self.pm = PaymentMethod.objects.create(
            code=PaymentMethodChoices.COD,
            name="Cash On Delivery"
        )
        # Get point wallet
        self.wallet = PointWalletRepository.get_or_create_for_customer(self.customer)

    def test_checkout_with_sufficient_tokens(self):
        from decimal import Decimal
        from apps.cart.models import Cart, CartItem
        from apps.orders.services import OrderService

        # Set wallet balance to 150 points (more than required 100 points)
        self.wallet.balance = 150
        self.wallet.save()

        # Create cart and add product
        cart = Cart.objects.create(customer=self.customer)
        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=1,
            price_snapshot=Decimal("500.00")
        )

        # Checkout
        order = OrderService.checkout(
            cart=cart,
            warehouse_id=self.warehouse.id,
            currency="INR",
            payment_method_code=self.pm.code,
        )

        # Since the customer has enough tokens (100 required, 150 available),
        # they pay the base price: ₹500 subtotal + ₹90 GST = ₹590 total.
        # No shortfall cash is added.
        expected_subtotal = Decimal("500.00")
        expected_gst = Decimal("90.00")
        expected_total = Decimal("590.00")

        self.assertEqual(order.total_amount, expected_total)
        self.assertEqual(order.gst, expected_gst)
        self.assertEqual(order.points_redeemed, 100)

        # Verify wallet balance decreased by 100
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 50)

        # Verify serialized token_shortfall_charge
        from apps.orders.api_v1.serializers import OrderSerializer
        serializer = OrderSerializer(order)
        self.assertEqual(Decimal(serializer.data["token_shortfall_charge"]), Decimal("0.00"))

    def test_checkout_with_insufficient_tokens(self):
        from decimal import Decimal
        from apps.cart.models import Cart, CartItem
        from apps.orders.services import OrderService

        # Set wallet balance to 40 points (shortfall of 60 points)
        self.wallet.balance = 40
        self.wallet.save()

        # Create cart and add product
        cart = Cart.objects.create(customer=self.customer)
        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=1,
            price_snapshot=Decimal("500.00")
        )

        # Checkout
        order = OrderService.checkout(
            cart=cart,
            warehouse_id=self.warehouse.id,
            currency="INR",
            payment_method_code=self.pm.code,
        )

        # Total required points = 100
        # Available points = 40
        # Shortfall = 60 points/tokens.
        # Shortfall cash value at 1 token = 1 rupee: ₹60.
        # New subtotal = ₹500 + ₹60 = ₹560.
        # GST = ₹560 * 18% = ₹100.80.
        # Total = ₹560 + ₹100.80 = ₹660.80.
        expected_total = Decimal("660.80")
        expected_gst = Decimal("100.80")

        self.assertEqual(order.total_amount, expected_total)
        self.assertEqual(order.gst, expected_gst)
        self.assertEqual(order.points_redeemed, 40)

        # Verify wallet balance decreased to 0
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 0)

        # Verify serialized token_shortfall_charge
        from apps.orders.api_v1.serializers import OrderSerializer
        serializer = OrderSerializer(order)
        self.assertEqual(Decimal(serializer.data["token_shortfall_charge"]), Decimal("60.00"))
