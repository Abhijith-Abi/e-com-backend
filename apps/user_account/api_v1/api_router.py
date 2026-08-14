from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.user_account.api_v1.views import (AdminRegisterView,
                                            CreateWarehouseAdminView,
                                            ForgotPasswordView,
                                            ListWarehouseAdminsView, LoginView,
                                            PrivilegeCardDetailView,
                                            PrivilegeCardListCreateView,
                                            ProfileView, RegisterUserView,
                                            ResendOTPView, ResetPasswordView,
                                            SelectWarehouseView,
                                            VerifyEmailView,
                                            WarehouseAdminDetailView,
                                            WarehouseAdminToggleActiveView)

app_name = "api_v1"

urlpatterns = [
    path("register/", RegisterUserView.as_view(), name="register"),
    path("verify-email/", VerifyEmailView.as_view(), name="verify-email"),
    path("resend-otp/", ResendOTPView.as_view(), name="resend-otp"),
    path("admin-register/", AdminRegisterView.as_view(), name="admin-register"),
    path("login/", LoginView.as_view(), name="login"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("create-admin/", CreateWarehouseAdminView.as_view(), name="create-admin"),
    path(
        "warehouse-admins/", ListWarehouseAdminsView.as_view(), name="warehouse-admins"
    ),
    path(
        "warehouse-admins/<uuid:pk>/",
        WarehouseAdminDetailView.as_view(),
        name="warehouse-admin-detail",
    ),
    path(
        "warehouse-admins/<uuid:pk>/toggle-active/",
        WarehouseAdminToggleActiveView.as_view(),
        name="warehouse-admin-toggle-active",
    ),
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot-password"),
    path("reset-password/", ResetPasswordView.as_view(), name="reset-password"),
    path("select-warehouse/", SelectWarehouseView.as_view(), name="select-warehouse"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    # Privilege Card
    path(
        "privilege-cards/",
        PrivilegeCardListCreateView.as_view(),
        name="privilege-card-list",
    ),
    path(
        "privilege-cards/<uuid:pk>/",
        PrivilegeCardDetailView.as_view(),
        name="privilege-card-detail",
    ),
]
