from apps.banners.models import Banner, Testimonial


class BannerRepository:
    @staticmethod
    def list_banners():
        return Banner.objects.select_related("warehouse").filter(is_deleted=False).order_by("-created_at")

    @staticmethod
    def list_banners_by_warehouse(warehouse_id):
        return (
            Banner.objects.select_related("warehouse")
            .filter(warehouse_id=warehouse_id)
            .order_by("-created_at")
        )

    @staticmethod
    def list_active_banners_by_warehouse(warehouse_id):
        return (
            Banner.objects.select_related("warehouse")
            .filter(warehouse_id=warehouse_id, status="active", is_active=True)
            .order_by("-created_at")
        )


class TestimonialRepository:
    @staticmethod
    def list_testimonials():
        return Testimonial.objects.select_related("warehouse").filter(status="active", is_active=True).order_by("-created_at")

    @staticmethod
    def list_testimonials_by_warehouse(warehouse_id):
        return (
            Testimonial.objects.select_related("warehouse")
            .filter(warehouse_id=warehouse_id, status="active", is_active=True)
            .order_by("-created_at")
        )
    @staticmethod
    def list_all_testimonials():
        return Testimonial.objects.select_related("warehouse").order_by("-created_at")

    @staticmethod
    def list_all_testimonials_by_warehouse(warehouse_id):
        return (
            Testimonial.objects.select_related("warehouse")
            .filter(warehouse_id=warehouse_id)
            .order_by("-created_at")
        )
