from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.user_account.models import UserRoleChoices


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.is_admin)


class IsAdminOrOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_authenticated and request.user.is_admin:
            return True
        owner = getattr(obj, "user", None) or getattr(obj, "customer", None)
        return owner == getattr(request.user, "customer_profile", None) or owner == request.user


class IsWarehouseAdminOrAdmin(BasePermission):
    """
    Allows access if:
    - user is a superadmin (role=admin), OR
    - user is a warehouse_admin whose selected_warehouse matches request.warehouse
    Read-only (SAFE_METHODS) is allowed for both roles.
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.role == UserRoleChoices.ADMIN:
            return True
        if user.role == UserRoleChoices.WAREHOUSE_ADMIN:
            warehouse = getattr(request, "warehouse", None)
            if warehouse and user.selected_warehouse_id == warehouse.id:
                return True
        return False


class IsActiveCustomer(BasePermission):
    """
    Allows access only if:
    - user is authenticated AND
    - user is NOT deleted AND
    - user.customer_profile is NOT suspended
    """

    message = "Your account has been suspended or deleted. Please contact support."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        
        # Check if user is deleted or inactive
        if not user.is_active or user.is_deleted:
            self.message = "Your account has been deleted."
            return False
        
        # Check if customer is suspended
        profile = getattr(user, "customer_profile", None)
        if profile and profile.is_suspended:
            self.message = "Your account has been suspended. Please contact support."
            return False
        
        return True
