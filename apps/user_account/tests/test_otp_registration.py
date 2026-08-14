from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core import mail
from rest_framework import status
from rest_framework.test import APITestCase

from apps.user_account.models import EmailOTP

User = get_user_model()


class OTPRegistrationTestCase(APITestCase):
    """Test cases for OTP registration flow and email verification"""

    def setUp(self):
        self.register_url = "/api/v1/auth/register/"
        self.verify_url = "/api/v1/auth/verify-email/"
        self.login_url = "/api/v1/auth/login/"
        self.resend_otp_url = "/api/v1/auth/resend-otp/"

    def test_registration_without_otp_flow(self):
        """Test registration completing immediately when is_normal_user is False (default)"""
        data = {
            "email": "immediate@example.com",
            "password": "testpassword123",
            "full_name": "Immediate User",
            "is_normal_user": False,
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["email"], "immediate@example.com")

        # Verify user is verified immediately
        user = User.objects.get(email="immediate@example.com")
        self.assertTrue(user.is_verified)

        # Test they can login immediately
        login_data = {"email": "immediate@example.com", "password": "testpassword123"}
        login_response = self.client.post(self.login_url, login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", login_response.data)

    @patch("resend.Emails.send")
    def test_registration_with_otp_flow(self, mock_resend_send):
        """Test registration flow with is_normal_user is True"""
        data = {
            "email": "normal@example.com",
            "password": "testpassword123",
            "full_name": "Normal User",
            "is_normal_user": True,
        }
        with self.settings(RESEND_API_KEY="test_key"):
            response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("detail", response.data)
        self.assertFalse(response.data["is_verified"])

        # Verify user is created but is_verified is False
        user = User.objects.get(email="normal@example.com")
        self.assertFalse(user.is_verified)

        # Test they CANNOT login before verifying email
        login_data = {"email": "normal@example.com", "password": "testpassword123"}
        login_response = self.client.post(self.login_url, login_data)
        self.assertEqual(login_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "Please verify your email address first.", str(login_response.data)
        )

        # Check that an OTP was generated
        otp_record = EmailOTP.objects.filter(user=user, is_used=False).first()
        self.assertIsNotNone(otp_record)
        self.assertEqual(len(otp_record.otp_code), 6)

        # Wait up to 1 second for the background thread to call resend
        import time
        for _ in range(10):
            if mock_resend_send.call_count >= 1:
                break
            time.sleep(0.1)

        self.assertGreaterEqual(mock_resend_send.call_count, 1)
        call_params = mock_resend_send.call_args[0][0]
        self.assertIn(otp_record.otp_code, call_params["text"])

        # Test verification fails with incorrect OTP
        verify_data = {"email": "normal@example.com", "otp_code": "000000"}
        verify_response = self.client.post(self.verify_url, verify_data)
        self.assertEqual(verify_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid or expired OTP.", str(verify_response.data))

        # Test verification succeeds with correct OTP
        verify_data = {"email": "normal@example.com", "otp_code": otp_record.otp_code}
        verify_response = self.client.post(self.verify_url, verify_data)
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", verify_response.data)
        self.assertIn("refresh", verify_response.data)
        self.assertEqual(verify_response.data["user"]["email"], "normal@example.com")

        # Verify user is now verified
        user.refresh_from_db()
        self.assertTrue(user.is_verified)

        # Verify OTP is marked as used
        otp_record.refresh_from_db()
        self.assertTrue(otp_record.is_used)

        # Test they can now login successfully
        login_response = self.client.post(self.login_url, login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", login_response.data)

    @patch("resend.Emails.send")
    def test_resend_otp_flow(self, mock_resend_send):
        """Test resending the OTP for an unverified user"""
        register_data = {
            "email": "resend_test@example.com",
            "password": "testpassword123",
            "full_name": "Resend Test User",
            "is_normal_user": True,
        }
        with self.settings(RESEND_API_KEY="test_key"):
            response = self.client.post(self.register_url, register_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(email="resend_test@example.com")
        first_otp = EmailOTP.objects.filter(user=user, is_used=False).first()
        self.assertIsNotNone(first_otp)

        mock_resend_send.reset_mock()
        resend_data = {"email": "resend_test@example.com"}
        with self.settings(RESEND_API_KEY="test_key"):
            resend_response = self.client.post(self.resend_otp_url, resend_data)
        self.assertEqual(resend_response.status_code, status.HTTP_200_OK)
        self.assertEqual(resend_response.data["email"], "resend_test@example.com")

        import time
        for _ in range(10):
            if mock_resend_send.call_count >= 1:
                break
            time.sleep(0.1)

        self.assertGreaterEqual(mock_resend_send.call_count, 1)

        first_otp.refresh_from_db()
        self.assertTrue(first_otp.is_used)

        new_otp = EmailOTP.objects.filter(user=user, is_used=False).first()
        self.assertIsNotNone(new_otp)
        self.assertNotEqual(first_otp.otp_code, new_otp.otp_code)
