import logging
import threading
import resend
from django.template.loader import render_to_string
from django.conf import settings

logger = logging.getLogger(__name__)

def send_order_confirmation_email(order, customer):
    """Send order confirmation email to customer asynchronously in a background thread using Resend"""
    try:
        logger.info(f"Starting email pre-rendering for order {order.order_id} to {customer.user.email}")
        
        # Email subject
        subject = f"Order Confirmed - {order.order_id}"
        
        # Email context with order details (rendered on the main thread to avoid database calls in background thread)
        context = {
            'order_id': order.order_id,
            'customer_name': customer.user.full_name or customer.user.email,
            'total_amount': order.total_amount,
            'currency': order.currency,
            'items_count': order.items.count(),
            'shipping_address': order.shipping_address,
        }
        
        # Render email template on main thread
        html_message = render_to_string('email/order_confirmation.html', context)
        recipient = customer.user.email
        from_email = settings.DEFAULT_FROM_EMAIL
        order_id = order.order_id
        
        # Define background task
        def send_bg():
            try:
                logger.info(f"Sending email via Resend in background thread for order {order_id} to {recipient}")
                resend.api_key = settings.RESEND_API_KEY
                
                params = {
                    "from": from_email,
                    "to": [recipient],
                    "subject": subject,
                    "text": f"Your order {order_id} has been processed!",
                    "html": html_message,
                }
                
                result = resend.Emails.send(params)
                logger.info(f"Background Resend email sent successfully for order {order_id}. Result: {result}")
            except Exception as e:
                logger.error(f"Error sending order confirmation email via Resend in background for order {order_id}: {str(e)}", exc_info=True)

        # Start thread
        thread = threading.Thread(target=send_bg)
        thread.daemon = True
        thread.start()
        logger.info(f"Spawned background thread to send email for order {order_id}")
        
    except Exception as e:
        logger.error(f"Error pre-rendering or spawning email thread for order {order.order_id}: {str(e)}", exc_info=True)
