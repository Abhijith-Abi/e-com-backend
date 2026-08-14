from apps.gift_cards.models import GiftCard, GiftCardCategory, GiftCardWrap


class GiftCardCategoryRepository:
    @staticmethod
    def list_categories():
        return GiftCardCategory.objects.select_related("warehouse").order_by("name")

    @staticmethod
    def list_categories_by_warehouse(warehouse_id):
        return (
            GiftCardCategory.objects.select_related("warehouse")
            .filter(warehouse_id=warehouse_id)
            .order_by("name")
        )


class GiftCardWrapRepository:
    @staticmethod
    def list_wraps():
        return GiftCardWrap.objects.select_related("warehouse").order_by("wrap_name")

    @staticmethod
    def list_wraps_by_warehouse(warehouse_id):
        return (
            GiftCardWrap.objects.select_related("warehouse")
            .filter(warehouse_id=warehouse_id)
            .order_by("wrap_name")
        )


class GiftCardRepository:
    @staticmethod
    def list_gift_cards():
        return GiftCard.objects.select_related("warehouse", "category").order_by("card_name")

    @staticmethod
    def list_gift_cards_by_warehouse(warehouse_id):
        return (
            GiftCard.objects.select_related("warehouse", "category")
            .filter(warehouse_id=warehouse_id)
            .order_by("card_name")
        )
