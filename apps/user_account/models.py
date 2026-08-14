import uuid

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from core.base_models import BaseModel


class UserRoleChoices(models.TextChoices):
    ADMIN = "admin", "Admin"
    WAREHOUSE_ADMIN = "warehouse_admin", "Warehouse Admin"
    CUSTOMER = "customer", "Customer"


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Email is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", UserRoleChoices.CUSTOMER)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_admin", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("role", UserRoleChoices.ADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_admin", True)
        extra_fields.setdefault("is_verified", True)
        extra_fields.setdefault("is_superuser", True)
        return self._create_user(email, password, **extra_fields)


class User(BaseModel, AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, db_index=True)
    full_name = models.CharField(max_length=255)
    role = models.CharField(
        max_length=20,
        choices=UserRoleChoices.choices,
        default=UserRoleChoices.CUSTOMER,
        db_index=True,
    )
    selected_warehouse = models.ForeignKey(
        "warehouses.Warehouse",
        on_delete=models.SET_NULL,
        related_name="assigned_users",
        null=True,
        blank=True,
    )
    is_admin = models.BooleanField(default=False, db_index=True)
    is_staff = models.BooleanField(default=False, db_index=True)
    is_verified = models.BooleanField(default=False, db_index=True)
    phone = models.CharField(max_length=20, null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    objects = UserManager()

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("email", "role")),
            models.Index(fields=("role", "selected_warehouse")),
        ]

    def save(self, *args, **kwargs):
        self.is_admin = self.role == UserRoleChoices.ADMIN
        self.is_staff = self.role in {
            UserRoleChoices.ADMIN,
            UserRoleChoices.WAREHOUSE_ADMIN,
        }
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email


class PrivilegeCard(BaseModel):
    full_name = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=30, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.full_name} ({self.phone})"


class PasswordResetToken(BaseModel):
    user = models.ForeignKey(
        "user_account.User",
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
    )
    token = models.UUIDField(
        default=uuid.uuid4, unique=True, editable=False, db_index=True
    )
    is_used = models.BooleanField(default=False, db_index=True)
    expires_at = models.DateTimeField(db_index=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.user.email} - {self.token}"


class Enquiry(BaseModel):
    name = models.CharField(max_length=255, null=True, blank=True)
    mobile = models.CharField(max_length=30, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    company = models.CharField(max_length=255, null=True, blank=True)
    subject = models.CharField(max_length=255, null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    enquiry_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-enquiry_date",)

    def __str__(self):
        return f"Enquiry from {self.name} - {self.subject}"


class EmailOTP(BaseModel):
    user = models.ForeignKey(
        "user_account.User",
        on_delete=models.CASCADE,
        related_name="email_otps",
    )
    otp_code = models.CharField(max_length=6)
    is_used = models.BooleanField(default=False, db_index=True)
    expires_at = models.DateTimeField(db_index=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.user.email} - {self.otp_code}"
