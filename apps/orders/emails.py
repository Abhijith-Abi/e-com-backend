import logging
import resend
from django.conf import settings

logger = logging.getLogger(__name__)

def send_order_confirmed_email(order):
    """
    Sends a formatted plain text confirmation email to the customer when their order is confirmed.
    No HTML template files are used.
    """
    try:
        recipient = order.customer.user.email
        if not recipient:
            logger.warning(f"Order {order.order_id} has no customer email address. Skipping email confirmation.")
            return

        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
        tracking_link = f"{frontend_url}/track?order_id={order.order_id}"

        # Generate items list formatted in plain text
        items_list = []
        for item in order.items.all():
            variant_info = ""
            if item.selected_color or item.selected_size:
                parts = []
                if item.selected_color:
                    parts.append(f"Color: {item.selected_color}")
                if item.selected_size:
                    parts.append(f"Size: {item.selected_size}")
                variant_info = f" ({', '.join(parts)})"
            
            items_list.append(
                f"- {item.product.name_en}{variant_info}\n"
                f"  Qty: {item.quantity} | Price: {order.currency} {item.price}"
            )
        items_text = "\n".join(items_list)

        # Generate discount section
        discount_text = ""
        if order.discount_amount:
            discount_text = f"Discount: - {order.currency} {order.discount_amount}\n"

        # Generate shipping address text
        address_text = "N/A"
        if order.shipping_address:
            addr = order.shipping_address
            addr_line2 = f"{addr.address_line2}\n" if addr.address_line2 else ""
            address_text = (
                f"{addr.full_name}\n"
                f"{addr.address_line1}\n"
                f"{addr_line2}"
                f"{addr.city}, {addr.state} {addr.postal_code}\n"
                f"{addr.country}\n"
                f"Phone: {addr.phone}"
            )

        message_body = (
            f"Dear {order.customer.user.full_name or 'Customer'},\n\n"
            f"Thank you for your purchase! We are pleased to confirm that your order has been received and is being prepared.\n\n"
            f"==========================================\n"
            f"ORDER SUMMARY\n"
            f"==========================================\n"
            f"Order ID: {order.order_id}\n"
            f"Order Date: {order.created_at.strftime('%B %d, %Y, %I:%M %p')}\n"
            f"Status: {order.order_status.upper()}\n\n"
            f"ITEMS:\n"
            f"{items_text}\n\n"
            f"{discount_text}"
            f"GST (18%): {order.currency} {order.gst}\n"
            f"Grand Total: {order.currency} {order.total_amount}\n"
            f"==========================================\n\n"
            f"SHIPPING ADDRESS:\n"
            f"{address_text}\n\n"
            f"==========================================\n\n"
            f"You can track your shipment using the link below:\n"
            f"{tracking_link}\n\n"
            f"If you have any questions, feel free to reply to this email.\n\n"
            f"Best regards,\n"
            f"Sebastian Store Team"
        )

        # Define background task
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com")
        order_id = order.order_id
        subject = f"Order Confirmed: {order_id}"

        import threading
        def send_bg():
            try:
                resend.api_key = settings.RESEND_API_KEY
                params = {
                    "from": from_email,
                    "to": [recipient],
                    "subject": subject,
                    "text": message_body,
                }
                result = resend.Emails.send(params)
                logger.info(f"Order confirmation email successfully sent in background via Resend for {order_id} to {recipient}. Result: {result}")
            except Exception as e:
                logger.error(f"Failed to send background order confirmation email via Resend for {order_id}: {str(e)}")

        thread = threading.Thread(target=send_bg)
        thread.daemon = True
        thread.start()
        logger.info(f"Spawned background thread to send status confirmation email for {order_id}")
    except Exception as e:
        logger.error(f"Failed to send order confirmation email for {order.order_id}: {str(e)}")
