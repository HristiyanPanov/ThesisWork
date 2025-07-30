from django import forms
from main.models import ProductSize
from main.models import Product
from .models import WishlistItem


class AddToWishlistForm(forms.Form):
    size_id = forms.IntegerField(required=True)

    def __init__(self, *args, product=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.product = product
        self.user = user

        if product:
            sizes = product.product_sizes.filter(stock__gt=0)
            self.fields['size_id'] = forms.ChoiceField(
                choices=[(ps.id, ps.size.name) for ps in sizes],
                required=True,
                initial=sizes.first().id
            )

    def save(self):
        size_id = self.cleaned_data['size_id']
        product_size = ProductSize.objects.get(id=size_id)

        # Create or get the wishlist item
        item, created = WishlistItem.objects.get_or_create(
            user=self.user,
            product=self.product,
            product_size=product_size
        )
        return item, created
