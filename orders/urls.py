from django.urls import path
from .views import CheckoutView, validate_discount_code

app_name = 'orders'

urlpatterns = [
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('api/validate-discount-code/', validate_discount_code, name='validate_discount_code'),
]