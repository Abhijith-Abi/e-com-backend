import logging
import random
import threading
from datetime import timedelta

from django.conf import settings
import resend
from django.template.loader import render_to_string
from django.utils import timezone

from apps.user_account.models import EmailOTP

logger = logging.getLogger(__name__)


def generate_and_send_otp(user):
    """
    Generate a 6-digit OTP, save it to the database, and send it to the user's email.
    """
    # Deactivate existing OTPs for the user
    EmailOTP.objects.filter(user=user, is_used=False).update(is_used=True)

    # Generate 6-digit numeric OTP code
    otp_code = f"{random.randint(100000, 999999)}"

    # Save OTP to database (valid for 10 minutes)
    expires_at = timezone.now() + timedelta(minutes=10)
    EmailOTP.objects.create(
        user=user,
        otp_code=otp_code,
        expires_at=expires_at,
    )

    # Pre-render email
    subject = "Verify your email - Sebastian Store"
    context = {
        "customer_name": user.full_name or user.email,
        "otp_code": otp_code,
        "expires_in": 10,
    }
    html_message = render_to_string("email/verify_otp.html", context)
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com")
    recipient = user.email

    def send_bg():
        try:
            resend.api_key = settings.RESEND_API_KEY
            if not resend.api_key:
                logger.error(f"Failed to send verification email to {recipient} via Resend: RESEND_API_KEY is empty or not configured in your .env file.")
                return
            params = {
                "from": from_email,
                "to": [recipient],
                "subject": subject,
                "text": f"Your email verification OTP is {otp_code}. It is valid for 10 minutes.",
                "html": html_message,
            }
            result = resend.Emails.send(params)
            logger.info(f"OTP verification email successfully sent to {recipient} via Resend. Result: {result}")
        except Exception as e:
            logger.error(f"Failed to send verification email to {recipient} via Resend: {str(e)}")

    thread = threading.Thread(target=send_bg)
    thread.daemon = True
    thread.start()

    return otp_code
