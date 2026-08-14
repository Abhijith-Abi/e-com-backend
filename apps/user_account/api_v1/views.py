from typing import cast

from django.conf import settings
from drf_spectacular.utils import (OpenApiParameter, extend_schema,
                                   inline_serializer)
from rest_framework import fields, generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.user_account.api_v1.serializers import (
    AuthUserSerializer, CreateWarehouseAdminSerializer, EnquirySerializer,
    ForgotPasswordSerializer, HouseOfVazTokenObtainPairSerializer,
    PrivilegeCardSerializer, RegisterUserSerializer, ResetPasswordSerializer,
    ResendOTPSerializer, SelectWarehouseSerializer, UpdateWarehouseAdminSerializer,
    VerifyEmailSerializer)
from apps.user_account.models import (Enquiry, PrivilegeCard, User,
                                      UserRoleChoices)


@extend_schema(tags=["Auth"], summary="Register a new customer account")
class RegisterUserView(generics.CreateAPIView):
    serializer_class = RegisterUserSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Check if the registered user requires email OTP verification
        if getattr(user, "_is_normal_user", False):
            from apps.user_account.functions import generate_and_send_otp

            generate_and_send_otp(user)

            return Response(
                {
                    "detail": "Verification OTP sent to your email. Please verify your email to complete registration.",
                    "is_verified": False,
                    "email": user.email,
                },
                status=status.HTTP_201_CREATED,
            )

        refresh = cast(RefreshToken, HouseOfVazTokenObtainPairSerializer.get_token(user))
        access_token = refresh.access_token

        profile = getattr(user, "customer_profile", None)
        return Response(
            {
                "detail": "Registration successful. Logged in.",
                "refresh": str(refresh),
                "access": str(access_token),
                "user": AuthUserSerializer(user).data,
                "role": user.role,
                "selected_warehouse_id": (
                    str(user.selected_warehouse_id)
                    if user.selected_warehouse_id
                    else None
                ),
                "customer_id": str(profile.id) if profile else None,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=["Auth"],
    summary="Verify email OTP to complete registration",
    request=VerifyEmailSerializer,
    responses={
        200: inline_serializer(
            name="VerifyEmailResponse",
            fields={
                "detail": fields.CharField(),
                "refresh": fields.CharField(),
                "access": fields.CharField(),
                "user": AuthUserSerializer,
                "role": fields.CharField(),
                "selected_warehouse_id": fields.CharField(allow_null=True),
                "customer_id": fields.CharField(allow_null=True),
            },
        )
    },
)
class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate custom JWT claims using the custom serializer get_token method
        refresh = cast(RefreshToken, HouseOfVazTokenObtainPairSerializer.get_token(user))
        access_token = refresh.access_token

        profile = getattr(user, "customer_profile", None)
        return Response(
            {
                "detail": "Email verified successfully. Registration complete.",
                "refresh": str(refresh),
                "access": str(access_token),
                "user": AuthUserSerializer(user).data,
                "role": user.role,
                "selected_warehouse_id": (
                    str(user.selected_warehouse_id)
                    if user.selected_warehouse_id
                    else None
                ),
                "customer_id": str(profile.id) if profile else None,
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(
    tags=["Auth"],
    summary="Resend verification OTP to complete registration",
    request=ResendOTPSerializer,
    responses={
        200: inline_serializer(
            name="ResendOTPResponse",
            fields={
                "detail": fields.CharField(),
                "email": fields.EmailField(),
            },
        )
    },
)
class ResendOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        user = User.objects.get(email=email, is_deleted=False)

        from apps.user_account.functions import generate_and_send_otp
        generate_and_send_otp(user)

        return Response(
            {
                "detail": "Verification OTP sent to your email. Please verify your email to complete registration.",
                "email": email,
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(tags=["Auth"], summary="Login and obtain JWT tokens")
class LoginView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]
    serializer_class = HouseOfVazTokenObtainPairSerializer


class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Auth"],
        summary="Get current user profile",
        responses={200: AuthUserSerializer},
    )
    def get(self, request):
        return Response(
            AuthUserSerializer(request.user).data, status=status.HTTP_200_OK
        )

    @extend_schema(
        tags=["Auth"],
        summary="Update current user profile (full_name, phone)",
        request=inline_serializer(
            name="UpdateProfileRequest",
            fields={
                "full_name": fields.CharField(required=False),
                "phone": fields.CharField(required=False),
            },
        ),
        responses={200: AuthUserSerializer},
    )
    def patch(self, request):
        allowed = ("full_name", "phone")
        for field in allowed:
            if field in request.data:
                setattr(request.user, field, request.data[field])
        request.user.save(
            update_fields=[f for f in allowed if f in request.data] + ["updated_at"]
        )
        return Response(
            AuthUserSerializer(request.user).data, status=status.HTTP_200_OK
        )


@extend_schema(tags=["Auth"], summary="Create a warehouse admin user (admin only)")
class CreateWarehouseAdminView(generics.CreateAPIView):
    serializer_class = CreateWarehouseAdminSerializer
    permission_classes = [permissions.IsAdminUser]


class AdminRegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=["Auth"],
        summary="Register an admin user (requires X-Admin-Secret header)",
        request=CreateWarehouseAdminSerializer,
        responses={201: AuthUserSerializer},
    )
    def post(self, request):
        if request.headers.get("X-Admin-Secret") != settings.ADMIN_REGISTRATION_SECRET:
            return Response(
                {"detail": "Invalid admin registration secret."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = CreateWarehouseAdminSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(AuthUserSerializer(user).data, status=status.HTTP_201_CREATED)


class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=["Auth"],
        summary="Request a password reset token",
        request=ForgotPasswordSerializer,
        responses={
            200: inline_serializer(
                name="ForgotPasswordResponse",
                fields={
                    "detail": fields.CharField(),
                    "token": fields.UUIDField(required=False),
                    "expires_at": fields.DateTimeField(required=False),
                },
            )
        },
    )
    def post(self, request):
        from django.conf import settings
        from django.core.mail import send_mail

        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reset_token = serializer.save()

        if reset_token:
            # In a real application, you might want to configure a FRONTEND_URL in settings
            # and build a full URL. Here we just send the token, which the frontend can use.
            frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
            reset_link = f"{frontend_url}/reset-password?token={reset_token.token}"

            import threading

            subject = "Password Reset Request"
            message = f"You requested a password reset. Click the link below to reset your password:\n\n{reset_link}\n\nThis link expires in 1 hour."
            from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com")
            recipient = reset_token.user.email

            def send_bg():
                try:
                    send_mail(
                        subject=subject,
                        message=message,
                        from_email=from_email,
                        recipient_list=[recipient],
                        fail_silently=True,
                    )
                except Exception:
                    pass

            thread = threading.Thread(target=send_bg)
            thread.daemon = True
            thread.start()

        return Response(
            {
                "detail": "If the account exists, a password reset link has been sent to your email."
            },
            status=status.HTTP_200_OK,
        )


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=["Auth"],
        summary="Reset password using a reset token",
        request=ResetPasswordSerializer,
        responses={
            200: inline_serializer(
                name="ResetPasswordResponse",
                fields={"detail": fields.CharField()},
            )
        },
    )
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Password updated successfully."}, status=status.HTTP_200_OK
        )


class SelectWarehouseView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Auth"],
        summary="Select active warehouse for the current user",
        request=SelectWarehouseSerializer,
        responses={200: AuthUserSerializer},
    )
    def post(self, request):
        serializer = SelectWarehouseSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(AuthUserSerializer(user).data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Auth"],
    summary="List all warehouse admins (admin only)",
    parameters=[
        OpenApiParameter(
            "warehouse", description="Filter by warehouse UUID", required=False
        ),
    ],
    responses={200: AuthUserSerializer(many=True)},
)
class ListWarehouseAdminsView(generics.ListAPIView):
    serializer_class = AuthUserSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        qs = User.objects.filter(role=UserRoleChoices.WAREHOUSE_ADMIN, is_deleted=False)
        warehouse_id = self.request.query_params.get("warehouse")
        if warehouse_id:
            qs = qs.filter(selected_warehouse_id=warehouse_id)
        return qs


def get_warehouse_admin_or_404(pk):
    from django.shortcuts import get_object_or_404

    return get_object_or_404(
        User, pk=pk, role=UserRoleChoices.WAREHOUSE_ADMIN, is_deleted=False
    )


@extend_schema(
    tags=["Auth"], summary="Retrieve, update or delete a warehouse admin (admin only)"
)
class WarehouseAdminDetailView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, pk):
        user = get_warehouse_admin_or_404(pk)
        return Response(AuthUserSerializer(user).data)

    @extend_schema(
        request=UpdateWarehouseAdminSerializer, responses={200: AuthUserSerializer}
    )
    def put(self, request, pk):
        user = get_warehouse_admin_or_404(pk)
        serializer = UpdateWarehouseAdminSerializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(AuthUserSerializer(user).data)

    @extend_schema(
        request=UpdateWarehouseAdminSerializer, responses={200: AuthUserSerializer}
    )
    def patch(self, request, pk):
        user = get_warehouse_admin_or_404(pk)
        serializer = UpdateWarehouseAdminSerializer(
            user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(AuthUserSerializer(user).data)

    def delete(self, request, pk):
        user = get_warehouse_admin_or_404(pk)
        user.is_deleted = True
        user.is_active = False
        user.save(update_fields=["is_deleted", "is_active", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=["Auth"],
    summary="Toggle active/inactive status of a warehouse admin (admin only)",
    responses={200: AuthUserSerializer},
)
class WarehouseAdminToggleActiveView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        user = get_warehouse_admin_or_404(pk)
        user.is_active = not user.is_active
        user.save(update_fields=["is_active", "updated_at"])
        return Response(AuthUserSerializer(user).data)


# ── Privilege Card ────────────────────────────────────────────────────────────


@extend_schema(
    tags=["Privilege Card"],
    summary="List all privilege card registrations or create a new one",
)
class PrivilegeCardListCreateView(generics.ListCreateAPIView):
    serializer_class = PrivilegeCardSerializer
    permission_classes = [permissions.AllowAny]
    queryset = PrivilegeCard.objects.filter(is_deleted=False)


@extend_schema(
    tags=["Privilege Card"],
    summary="Retrieve, update or delete a privilege card registration",
)
class PrivilegeCardDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PrivilegeCardSerializer
    permission_classes = [permissions.AllowAny]
    queryset = PrivilegeCard.objects.filter(is_deleted=False)

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.is_active = False
        instance.save(update_fields=["is_deleted", "is_active", "updated_at"])


# ── Enquiry / Contact Page ──────────────────────────────────────────────────

import django_filters
import django_filters.rest_framework
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination


class EnquiryFilter(django_filters.rest_framework.FilterSet):
    name__icontains = django_filters.CharFilter(
        field_name="name", lookup_expr="istartswith"
    )
    company__icontains = django_filters.CharFilter(
        field_name="company", lookup_expr="icontains"
    )
    email__icontains = django_filters.CharFilter(
        field_name="email", lookup_expr="icontains"
    )
    mobile__icontains = django_filters.CharFilter(
        field_name="mobile", lookup_expr="icontains"
    )
    subject__icontains = django_filters.CharFilter(
        field_name="subject", lookup_expr="icontains"
    )
    is_active = django_filters.BooleanFilter(field_name="is_active")

    class Meta:
        model = Enquiry
        fields = []


class EnquiryPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response(
            {
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "total_pages": self.page.paginator.num_pages,
                "current_page": self.page.number,
                "page_size": self.page.paginator.per_page,
                "results": data,
            }
        )


@extend_schema(tags=["Enquiry"])
class EnquiryViewSet(viewsets.ModelViewSet):
    queryset = Enquiry.objects.filter(is_deleted=False).order_by("-enquiry_date")
    serializer_class = EnquirySerializer
    pagination_class = EnquiryPagination
    filter_backends = (
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter,  # ← ADD THIS LINE
        filters.OrderingFilter,
    )
    filterset_class = EnquiryFilter
    search_fields = ["name", "email", "subject", "message"]
    ordering_fields = ("name", "enquiry_date")

    def get_permissions(self):
        if self.action in [
            "list",
            "retrieve",
            "search",
            "filter_by_date",
            "filter_by_company",
            "stats",
        ]:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {"status": "success", "data": serializer.data},
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(
            {"status": "success", "data": serializer.data}, status=status.HTTP_200_OK
        )

    # ── Custom Actions ────────────────────────────────────────────────────────────

    @action(detail=False, methods=["post"], permission_classes=[permissions.AllowAny])
    def public_submit(self, request):
        """Dedicated user side public contact submission API"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            {
                "status": "success",
                "message": "Your contact enquiry has been submitted.",
                "data": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"])
    def search(self, request):
        from django.db.models import Q

        q = request.query_params.get("q")
        if not q:
            return Response(
                {"error": "Query parameter 'q' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = self.get_queryset().filter(
            Q(name__istartswith=q)
            | Q(mobile__icontains=q)
            | Q(email__icontains=q)
            | Q(company__icontains=q)
            | Q(subject__icontains=q)
            | Q(message__icontains=q)
        )
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def filter_by_date(self, request):
        from_date = request.query_params.get("from_date")
        to_date = request.query_params.get("to_date")

        qs = self.get_queryset()
        if from_date:
            qs = qs.filter(enquiry_date__date__gte=from_date)
        if to_date:
            qs = qs.filter(enquiry_date__date__lte=to_date)

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def filter_by_company(self, request):
        company = request.query_params.get("company")
        if not company:
            return Response(
                {"error": "Query parameter 'company' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = self.get_queryset().filter(company__icontains=company)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def bulk_delete(self, request):
        try:
            ids = request.data.get("ids", [])
            if hasattr(request.data, "getlist"):
                qd_ids = request.data.getlist("ids")
                if qd_ids:
                    ids = qd_ids

            if isinstance(ids, str):
                if ids.startswith("[") and ids.endswith("]"):
                    import json

                    try:
                        ids = json.loads(ids)
                    except ValueError:
                        ids = [x.strip(" '\"") for x in ids[1:-1].split(",")]
                else:
                    ids = [x.strip() for x in ids.split(",") if x.strip()]

            valid_ids = []
            import uuid

            for item in ids:
                try:
                    clean_item = str(item).strip(" '\"[]\t\n")
                    if clean_item:
                        uuid.UUID(clean_item)
                        valid_ids.append(clean_item)
                except ValueError:
                    pass

            if not valid_ids:
                return Response(
                    {"error": "No valid IDs provided."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            Enquiry.objects.filter(id__in=valid_ids).delete()
            return Response(
                {"status": "success", "message": "Enquiries successfully deleted."},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            import traceback

            return Response(
                {"error": str(e), "traceback": traceback.format_exc()},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["get"])
    def stats(self, request):
        total = Enquiry.objects.filter(is_deleted=False).count()
        active = Enquiry.objects.filter(is_deleted=False, is_active=True).count()
        unique_cities = (
            Enquiry.objects.filter(is_deleted=False)
            .values("company")
            .distinct()
            .count()
        )

        return Response(
            {
                "status": "success",
                "data": {
                    "total_enquiries": total,
                    "active_enquiries": active,
                    "unique_cities": unique_cities,
                },
            }
        )
