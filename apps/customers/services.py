from apps.customers.models import CustomerProfile


class CustomerService:
    @staticmethod
    def ensure_profile(user):
        profile, _ = CustomerProfile.objects.get_or_create(user=user)
        return profile
