# wishlist/urls.py
from django.urls import path
from . import views

app_name = "wishlist"

urlpatterns = [
    path('add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path("remove/<int:item_id>/", views.remove_from_wishlist, name="remove"),
    path("modal/", views.wishlist_modal, name="modal"),
    path("count/", views.wishlist_count, name="count"),
    path("clear/", views.clear_wishlist, name="clear"),
    path("notification/<int:product_id>/", views.wishlist_notification, name="notification"),
]
