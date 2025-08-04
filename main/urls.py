from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('catalog/', views.CatalogView.as_view(), name='catalog_all'),
    path('catalog/<slug:category_slug>/', views.CatalogView.as_view(), name='catalog'),
    path('product/<slug:slug>', views.ProductDetailView.as_view(), name='product_detail'),
    path('submit-review/<int:product_id>/', views.submit_review, name='submit_review'),

]
