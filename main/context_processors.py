from .models import Category

def categories(request):
    return {
        'categories': Category.objects.filter(parent__isnull=True).prefetch_related('subcategories')
    }
