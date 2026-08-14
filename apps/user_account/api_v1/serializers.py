from datetime import timedelta
from typing import cast

from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from apps.customers.models import CustomerProfile
from apps.user_account.models import (Enquiry, PasswordResetToken,
                                      PrivilegeCard, User, UserRoleChoices)
from apps.warehouses.models import Warehouse
from core.choices import LanguageChoices, RegionChoices


class AuthUserSerializer(serializers.ModelSerializer):
    selected_warehouse_name = serializers.CharField(
        source="selected_warehouse.warehouse_name", read_only=True
    )
    selected_warehouse_location = serializers.CharField(
        source="selected_warehouse.warehouse_location", read_only=True
    )

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "full_name",
            "phone",
            "role",
            "selected_warehouse",
            "selected_warehouse_name",
            "selected_warehouse_location",
            "is_verified",
            "is_active",
        )


class RegisterUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    preferred_language = serializers.ChoiceField(
        choices=LanguageChoices.choices,
        default=LanguageChoices.ENGLISH,
        write_only=True,
    )
    country = serializers.ChoiceField(
        choices=RegionChoices.choices,
        default=RegionChoices.INDIA,
        write_only=True,
    )
    is_normal_user = serializers.BooleanField(default=False, write_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "password",
            "full_name",
            "phone",
            "preferred_language",
            "country",
            "customer_id",
            "is_normal_user",
        )
        read_only_fields = ("id",)

    customer_id = serializers.SerializerMethodField()

    def get_customer_id(self, instance):
        if hasattr(instance, "_customer_profile_id"):
            return str(instance._customer_profile_id)
        return None

    def create(self, validated_data):
        is_normal_user = validated_data.pop("is_normal_user", False)

        preferred_language = validated_data.pop(
            "preferred_language", LanguageChoices.ENGLISH
        )
        country = validated_data.pop("country", RegionChoices.INDIA)

        if not is_normal_user:
            validated_data["is_verified"] = True
        else:
            validated_data["is_verified"] = False

        user = User.objects.create_user(**validated_data)
        profile = CustomerProfile.objects.create(
            user=user,
            preferred_language=preferred_language,
            country=country,
            preferred_currency="INR",
        )
        user._customer_profile_id = profile.id
        user._is_normal_user = is_normal_user
        return user


class CreateWarehouseAdminSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("id", "email", "password", "full_name", "role", "selected_warehouse")
        read_only_fields = ("id",)

    def validate_role(self, value):
        if value not in {UserRoleChoices.ADMIN, UserRoleChoices.WAREHOUSE_ADMIN}:
            raise serializers.ValidationError("Role must be admin or warehouse_admin.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        validated_data.setdefault("is_verified", True)
        return User.objects.create_user(password=password, **validated_data)


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def save(self):
        user = User.objects.filter(
            email=self.validated_data["email"], is_active=True, is_deleted=False
        ).first()
        if not user:
            return None
        return PasswordResetToken.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(hours=1),
        )


class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6, min_length=6)

    def validate(self, attrs):
        from django.utils import timezone

        from apps.user_account.models import EmailOTP

        email = attrs.get("email")
        otp_code = attrs.get("otp_code")

        user = User.objects.filter(email=email, is_deleted=False).first()
        if not user:
            raise serializers.ValidationError(
                {"email": "User with this email does not exist."}
            )

        # Find the latest unused, active, non-expired OTP for the user
        otp_record = EmailOTP.objects.filter(
            user=user,
            otp_code=otp_code,
            is_used=False,
            expires_at__gte=timezone.now(),
        ).first()

        if not otp_record:
            raise serializers.ValidationError({"otp_code": "Invalid or expired OTP."})

        attrs["user"] = user
        attrs["otp_record"] = otp_record
        return attrs

    def save(self):
        user = self.validated_data["user"]
        otp_record = self.validated_data["otp_record"]

        # Mark user as verified
        user.is_verified = True
        user.save(update_fields=["is_verified", "updated_at"])

        # Mark OTP as used
        otp_record.is_used = True
        otp_record.save(update_fields=["is_used", "updated_at"])

        return user


class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        user = User.objects.filter(email=value, is_deleted=False).first()
        if not user:
            raise serializers.ValidationError("User with this email does not exist.")
        if user.is_verified:
            raise serializers.ValidationError("This email is already verified.")
        return value


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    new_password = serializers.CharField(min_length=8)

    def validate(self, attrs):
        reset_token = (
            PasswordResetToken.objects.filter(
                token=attrs["token"],
                is_used=False,
                expires_at__gte=timezone.now(),
                user__is_active=True,
            )
            .select_related("user")
            .first()
        )
        if not reset_token:
            raise serializers.ValidationError({"token": "Invalid or expired token."})
        attrs["reset_token"] = reset_token
        return attrs

    def save(self):
        reset_token = self.validated_data["reset_token"]
        user = reset_token.user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        reset_token.is_used = True
        reset_token.save(update_fields=["is_used", "updated_at"])
        return user


class SelectWarehouseSerializer(serializers.Serializer):
    warehouse_id = serializers.UUIDField()

    def validate_warehouse_id(self, value):
        if not Warehouse.objects.filter(
            id=value, is_active=True, is_deleted=False
        ).exists():
            raise serializers.ValidationError("Warehouse not found.")
        return value

    def save(self, **kwargs):
        user = self.context["request"].user
        user.selected_warehouse_id = self.validated_data["warehouse_id"]
        user.save(
            update_fields=["selected_warehouse", "is_admin", "is_staff", "updated_at"]
        )
        return user


class UpdateWarehouseAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("full_name", "email", "selected_warehouse", "role")

    def validate_role(self, value):
        if value not in {UserRoleChoices.ADMIN, UserRoleChoices.WAREHOUSE_ADMIN}:
            raise serializers.ValidationError("Role must be admin or warehouse_admin.")
        return value


class HouseOfVazTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = "email"
    remember_me = serializers.BooleanField(
        required=False, default=False, write_only=True
    )

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["role"] = user.role
        token["full_name"] = user.full_name
        token["selected_warehouse_id"] = (
            str(user.selected_warehouse_id) if user.selected_warehouse_id else None
        )
        token["selected_warehouse_name"] = (
            user.selected_warehouse.warehouse_name
            if user.selected_warehouse_id
            else None
        )
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        profile = getattr(self.user, "customer_profile", None)
        if profile and profile.is_suspended:
            raise serializers.ValidationError(
                {"detail": "Your account has been suspended."}
            )
        if not self.user.is_active or self.user.is_deleted:
            raise serializers.ValidationError(
                {"detail": "Your account has been deleted."}
            )
        if not self.user.is_verified:
            raise serializers.ValidationError(
                {"detail": "Please verify your email address first."}
            )

        remember_me = attrs.get("remember_me", False)
        refresh = cast(RefreshToken, self.get_token(self.user))

        if remember_me:
            # Set a longer lifetime, e.g., 30 days
            refresh.set_exp(lifetime=timedelta(days=30))
        else:
            # Set a standard lifetime, e.g., 1 day
            refresh.set_exp(lifetime=timedelta(days=1))

        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)

        data["user"] = AuthUserSerializer(self.user).data
        data["role"] = self.user.role
        data["selected_warehouse_id"] = (
            str(self.user.selected_warehouse_id)
            if self.user.selected_warehouse_id
            else None
        )
        data["customer_id"] = str(profile.id) if profile else None
        return data


class PrivilegeCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivilegeCard
        fields = (
            "id",
            "full_name",
            "phone",
            "email",
            "city",
            "notes",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class EnquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = Enquiry
        fields = (
            "id",
            "name",
            "mobile",
            "email",
            "company",
            "subject",
            "message",
            "enquiry_date",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "enquiry_date", "created_at", "updated_at")
