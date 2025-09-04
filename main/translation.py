from modeltranslation.translator import translator, TranslationOptions
from .models import Category, Size, Product, ProductReview, Outfit

class CategoryTR(TranslationOptions):
    fields = ('name',)

class SizeTR(TranslationOptions):
    fields = ('name',)

class ProductTR(TranslationOptions):
    fields = ('name', 'color', 'description',)

class ProductReviewTR(TranslationOptions):
    fields = ('title', 'content',)

class OutfitTR(TranslationOptions):
    fields = ('title',)

translator.register(Category, CategoryTR)
translator.register(Size, SizeTR)
translator.register(Product, ProductTR)
translator.register(ProductReview, ProductReviewTR)
translator.register(Outfit, OutfitTR)
