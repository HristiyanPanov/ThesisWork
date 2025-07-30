from django.conf import settings
from django.db import models
from main.models import Product, ProductSize  # <- вече потвърдихме, че това са правилните модели


class WishlistItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wishlist_items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='wishlisted_in'
    )
    product_size = models.ForeignKey(
        ProductSize,
        on_delete=models.CASCADE,
        related_name='wishlisted_items'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product', 'product_size')
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.user} → {self.product.name} ({self.product_size.size.name})'
