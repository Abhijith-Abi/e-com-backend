class GiftCardService:
    @staticmethod
    def decrement_gift_card_units(gift_card, quantity):
        """Decrement gift card units and check for low stock"""
        gift_card.units = max(gift_card.units - quantity, 0)
        gift_card.save(update_fields=["units", "updated_at"])
        
        # Check if units are low and create notification
        GiftCardService.check_and_create_low_stock_notification(gift_card)
    
    @staticmethod
    def check_and_create_low_stock_notification(gift_card):
        """Create a low stock notification if units fall below or equal threshold"""
        from apps.gift_cards.models import LowStockGiftCardNotification
        
        if gift_card.units <= gift_card.reminder_threshold and gift_card.units > 0 and gift_card.reminder_threshold > 0:
            # Check if there's already an unread notification for this unit level
            existing = LowStockGiftCardNotification.objects.filter(
                gift_card=gift_card,
                remaining_units=gift_card.units,
                is_read=False
            ).exists()
            
            if not existing:
                message = f"{gift_card.card_name} has {gift_card.units} unit(s) left"
                LowStockGiftCardNotification.objects.create(
                    gift_card=gift_card,
                    remaining_units=gift_card.units,
                    threshold=gift_card.reminder_threshold,
                    message=message
                )
        elif gift_card.units == 0:
            # Out of stock notification
            existing = LowStockGiftCardNotification.objects.filter(
                gift_card=gift_card,
                remaining_units=0,
                is_read=False
            ).exists()
            
            if not existing:
                message = f"{gift_card.card_name} is OUT OF STOCK"
                LowStockGiftCardNotification.objects.create(
                    gift_card=gift_card,
                    remaining_units=0,
                    threshold=gift_card.reminder_threshold,
                    message=message
                )
    
    @staticmethod
    def decrement_gift_card_wrap_units(gift_card_wrap, quantity):
        """Decrement gift card wrap units and check for low stock"""
        gift_card_wrap.units = max(gift_card_wrap.units - quantity, 0)
        gift_card_wrap.save(update_fields=["units", "updated_at"])
        
        # Check if units are low and create notification
        GiftCardService.check_and_create_low_stock_wrap_notification(gift_card_wrap)
    
    @staticmethod
    def check_and_create_low_stock_wrap_notification(gift_card_wrap):
        """Create a low stock notification for wrap if units fall below or equal threshold"""
        from apps.gift_cards.models import LowStockGiftCardWrapNotification
        
        if gift_card_wrap.units <= gift_card_wrap.reminder_threshold and gift_card_wrap.units > 0 and gift_card_wrap.reminder_threshold > 0:
            # Check if there's already an unread notification for this unit level
            existing = LowStockGiftCardWrapNotification.objects.filter(
                gift_card_wrap=gift_card_wrap,
                remaining_units=gift_card_wrap.units,
                is_read=False
            ).exists()
            
            if not existing:
                message = f"{gift_card_wrap.wrap_name} has {gift_card_wrap.units} unit(s) left"
                LowStockGiftCardWrapNotification.objects.create(
                    gift_card_wrap=gift_card_wrap,
                    remaining_units=gift_card_wrap.units,
                    threshold=gift_card_wrap.reminder_threshold,
                    message=message
                )
        elif gift_card_wrap.units == 0:
            # Out of stock notification
            existing = LowStockGiftCardWrapNotification.objects.filter(
                gift_card_wrap=gift_card_wrap,
                remaining_units=0,
                is_read=False
            ).exists()
            
            if not existing:
                message = f"{gift_card_wrap.wrap_name} is OUT OF STOCK"
                LowStockGiftCardWrapNotification.objects.create(
                    gift_card_wrap=gift_card_wrap,
                    remaining_units=0,
                    threshold=gift_card_wrap.reminder_threshold,
                    message=message
                )
