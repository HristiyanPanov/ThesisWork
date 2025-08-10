# main/forms.py

from django import forms
from .models import ProductReview

class ProductReviewForm(forms.ModelForm):
    class Meta:
        model = ProductReview
        fields = ['rating', 'title', 'content']

        widgets = {
            'rating': forms.Select(choices=[(i, '★' * i) for i in range(1, 6)]),
            'title': forms.TextInput(attrs={'placeholder': 'Summary of your review'}),
            'content': forms.Textarea(attrs={'placeholder': 'Write your review...'}),
        }


class NewsletterForm(forms.Form):
    email = forms.EmailField(label='Email')