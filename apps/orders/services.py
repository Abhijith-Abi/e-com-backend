from decimal import Decimal
from uuid import uuid4

from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.cart.models import CartItem
from apps.orders.models import Order, OrderItem
from apps.payments.models import Payment, PaymentMethod
from apps.products.services import ProductService
from apps.warehouses.models import Warehouse
from core.choices import PaymentStatusChoices


class OrderService:
    @staticmethod
    def generate_order_id():
        import time
        ts = hex(int(time.time() * 1000))[-6:].upper()
        return f"HOV-{uuid4().hex[:8].upper()}{ts}"

    @classmethod
    @transaction.atomic
    def checkout(cls, cart, warehouse_id, currency=None, address_id=None, address_data=None, payment_method_code=None, coupon_code=None, points_to_redeem=0, gift_wrap_id=None, gift_card_id=None):
        from apps.customers.models import CustomerAddress

        cart_items = list(
            CartItem.objects.select_related("product", "cart__customer")
            .filter(cart=cart)
        )
        if not cart_items:
            raise ValidationError("Cannot checkout an empty cart.")

        warehouse = Warehouse.objects.filter(id=warehouse_id).first()
        if not warehouse:
            raise ValidationError("Warehouse not found.")
        customer = cart.customer
        active_currency = currency or customer.preferred_currency

        # Re-snapshot prices at checkout time using the active currency
        currency_price_field = {
            "INR": lambda p: p.sale_price_inr or p.price_inr,
            "GBP": lambda p: p.sale_price_gbp or p.price_gbp,
            "USD": lambda p: p.sale_price_usd or p.price_usd,
        }
        get_price = currency_price_field.get(active_currency, currency_price_field["INR"])
        for item in cart_items:
            item.price_snapshot = Decimal(str(get_price(item.product) or 0))

        subtotal = sum((item.price_snapshot * item.quantity for item in cart_items), Decimal("0.00"))
        
        # ═══════════════════════════════════════════════════════════════════════════════
        # HYBRID POINTS SYSTEM: Calculate required points and handle shortfall
        # ═══════════════════════════════════════════════════════════════════════════════
        total_required_points = sum((item.product.required_points or 0) * item.quantity for item in cart_items)
        from apps.redeem.repositories import RedeemSettingsRepository
        from apps.redeem.services import PointWalletService
        redeem_settings = RedeemSettingsRepository.get_active()
        
        # Get customer's current wallet balance
        wallet = None
        points_available = 0
        points_to_deduct = 0
        points_shortfall = 0
        shortfall_cash_value = Decimal("0.00")
        
        if total_required_points > 0:
            from apps.redeem.repositories import PointWalletRepository
            wallet = PointWalletRepository.get_or_create_for_customer(customer)
            points_available = wallet.balance
            
            # Deduct available points (up to what's required)
            points_to_deduct = min(total_required_points, points_available)
            
            # Calculate shortfall if customer doesn't have enough points
            points_shortfall = max(0, total_required_points - points_available)
            
            # Convert shortfall to cash value: 1 token = 1 rupees
            if points_shortfall > 0:
                shortfall_cash_value = Decimal(str(points_shortfall)).quantize(Decimal("0.01"))
        
        # Add shortfall cash to subtotal
        subtotal = subtotal + shortfall_cash_value

        # Apply coupon discount - will be reapplied after points calculation
        coupon = None

        # Resolve gift wrap and gift card packing
        gift_wrap = None
        gift_card = None
        gift_wrap_charges = Decimal("0.00")

        if gift_wrap_id:
            from apps.gift_cards.models import GiftCardWrap
            gift_wrap = GiftCardWrap.objects.filter(id=gift_wrap_id).first()
            if gift_wrap:
                price_map = {"INR": gift_wrap.price_inr, "GBP": gift_wrap.price_gbp, "USD": gift_wrap.price_usd}
                gift_wrap_charges += Decimal(str(price_map.get(active_currency) or 0))

        if gift_card_id:
            from apps.gift_cards.models import GiftCard
            gift_card = GiftCard.objects.filter(id=gift_card_id).first()
            if gift_card:
                price_map = {"INR": gift_card.price_inr, "GBP": gift_card.price_gbp, "USD": gift_card.price_usd}
                gift_wrap_charges += Decimal(str(price_map.get(active_currency) or 0))

        # 10% combo discount if both wrap and card selected
        if gift_wrap and gift_card:
            gift_wrap_charges = (gift_wrap_charges * Decimal("0.90")).quantize(Decimal("0.01"))

        # Apply points redemption - AUTOMATIC (no longer optional)
        # Points are ALWAYS deducted if customer has them
        redeemed_points = points_to_deduct
        points_discount = Decimal("0.00")  # No discount, points are mandatory payment

        # Apply coupon to final subtotal (recalculate if needed)
        coupon = None
        discount_amount = Decimal("0.00")
        final_subtotal = subtotal  # Already includes shortfall cash value
        
        if coupon_code:
            from apps.coupons.repositories import CouponRepository
            from core.choices import CouponTypeChoices
            currency_to_region = {"INR": "INDIA", "GBP": "UK", "USD": "USA"}
            region = currency_to_region.get(active_currency, "INDIA")
            coupon = CouponRepository.get_valid_coupon(coupon_code, region, customer=customer)
            if coupon is None:
                raise ValidationError("Invalid, expired, or already used coupon code.")
            if coupon.coupon_type == CouponTypeChoices.PERCENTAGE:
                if coupon.coupon_value > Decimal("100"):
                    raise ValidationError("Invalid coupon: percentage discount cannot exceed 100%.")
                discount_amount = (final_subtotal * coupon.coupon_value / Decimal("100")).quantize(Decimal("0.01"))
            else:
                # Validate fixed coupon amount
                if coupon.coupon_value > final_subtotal:
                    raise ValidationError(f"Coupon discount (₹{coupon.coupon_value}) cannot exceed product total (₹{final_subtotal}). Please use a smaller coupon or add more items to your cart.")
                discount_amount = coupon.coupon_value

        final_subtotal = final_subtotal - discount_amount

        # Calculate GST on final subtotal + gift_wrap_charges
        base_for_gst = final_subtotal + gift_wrap_charges
        gst = (base_for_gst * Decimal("0.18")).quantize(Decimal("0.01"))

        # Resolve shipping address
        shipping_address = None
        if address_id:
            # Use existing address by ID
            shipping_address = CustomerAddress.objects.filter(id=address_id, customer=customer).first()
        elif address_data:
            # Create new address from provided data
            shipping_address = CustomerAddress.objects.create(
                customer=customer,
                full_name=address_data.get("full_name", ""),
                phone=address_data.get("phone", ""),
                address_line1=address_data.get("address_line1", ""),
                address_line2=address_data.get("address_line2", ""),
                city=address_data.get("city", ""),
                state=address_data.get("state", ""),
                postal_code=address_data.get("postal_code", ""),
                country=address_data.get("country", ""),
                is_default=False,
            )
        else:
            # Fall back to default address
            shipping_address = customer.addresses.filter(is_default=True).first()

       
        # Resolve payment method
        pm = None
        if payment_method_code:
            pm = PaymentMethod.objects.filter(code=payment_method_code, is_active=True).first()
        if pm is None:
            pm = PaymentMethod.objects.filter(is_active=True).order_by("name").first()

        from django.db import IntegrityError
        order = None
        for attempt in range(5):
            try:
                with transaction.atomic():
                    order = Order.objects.create(
                        order_id=cls.generate_order_id(),
                        customer=customer,
                        warehouse=warehouse,
                        shipping_address=shipping_address,
                        currency=active_currency,
                        total_amount=final_subtotal + gst + gift_wrap_charges,
                        gst=gst,
                        applied_coupon=coupon,
                        discount_amount=discount_amount,  # Only coupon discount, not points
                        points_redeemed=redeemed_points,
                        applied_gift_wrap=gift_wrap,
                        applied_gift_card=gift_card,
                        gift_wrap_charges=gift_wrap_charges,
                    )
                break
            except IntegrityError as e:
                if "UNIQUE constraint failed: orders_order.order_id" in str(e) and attempt < 4:
                    continue
                raise

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.price_snapshot,
                selected_color=item.selected_color,
                selected_size=item.selected_size,
            )
            ProductService.decrement_stock(
                item.product,
                item.quantity,
                selected_color=item.selected_color,
                selected_size=item.selected_size
            )

        # ADD THIS HERE ↓
        # Decrement gift card and wrap stock
        if gift_wrap:
            gift_wrap.units -= 1
            gift_wrap.save()

        if gift_card:
            gift_card.units -= 1
            gift_card.save()
        # ADD THIS HERE ↑


        Payment.objects.create(
            order=order,
            payment_method=pm,
            payment_status=PaymentStatusChoices.PENDING,
        )
        CartItem.objects.filter(cart=cart).delete()

        # Record coupon usage to prevent reuse by the same customer
        if coupon:
            from apps.coupons.repositories import CouponRepository
            CouponRepository.record_coupon_usage(coupon, customer, order)

        # Debit redeemed points from wallet
        if redeemed_points > 0:
            from apps.redeem.services import PointWalletService
            PointWalletService.debit_points(
                customer=customer,
                points=redeemed_points,
                description=f"Redeemed for order {order.order_id}",
                order=order,
            )

        # Send order confirmation email
        from apps.orders.email_service import send_order_confirmation_email
        transaction.on_commit(lambda: send_order_confirmation_email(order, customer))

        return order
