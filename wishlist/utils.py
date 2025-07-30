from .models import WishlistItem

def all_items(user):
    return WishlistItem.objects.filter(user=user)
