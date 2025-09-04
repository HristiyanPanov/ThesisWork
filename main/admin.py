from django.contrib import admin
from modeltranslation.admin import TranslationAdmin  # 👈 ново
from .translation import *  # noqa  <-- гарантира, че моделите са регистрирани за превод

from .models import (
    Category, Size, Product, ProductImage, ProductSize,
    ProductReview, Outfit, OutfitItem, OutfitImage, NewsletterSubscriber
)

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 0

class ProductAdmin(TranslationAdmin):  # 👈 беше ModelAdmin
    list_display = ['name', 'category', 'color', 'price']
    list_filter = ['category', 'color']
    search_fields = ['name', 'color', 'description']
    prepopulated_fields = {'slug': ('name',)}  # slug остава общ
    inlines = [ProductImageInline, ProductSizeInline]

class CategoryAdmin(TranslationAdmin):  # 👈 беше ModelAdmin
    list_display = ['name', 'slug', 'parent']
    list_filter = ['parent']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']

class SizeAdmin(TranslationAdmin):
    list_display = ['name']

class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'title', 'created_at')
    search_fields = ('product__name', 'user__email', 'title', 'content')
    list_filter = ('rating', 'created_at')

class OutfitItemInline(admin.TabularInline):
    model = OutfitItem
    extra = 1

class OutfitImageInline(admin.TabularInline):
    model = OutfitImage
    extra = 1

class OutfitAdmin(TranslationAdmin):  # 👈 ако превеждаш Outfit.title
    list_display = ['title', 'gender', 'created_at']
    list_filter = ['gender']
    inlines = [OutfitItemInline, OutfitImageInline]

@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'discount_code', 'date_subscribed')
    search_fields = ('email',)
    list_filter = ('date_subscribed',)

admin.site.register(Category, CategoryAdmin)
admin.site.register(Size, SizeAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductReview, ProductReviewAdmin)
admin.site.register(Outfit, OutfitAdmin)
