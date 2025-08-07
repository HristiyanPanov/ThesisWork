from django.shortcuts import get_object_or_404, render
from django.views.generic import TemplateView, DetailView
from django.http import HttpResponse, JsonResponse
from django.template.response import TemplateResponse
from .models import Category, Product, Size, ProductReview, Outfit, ProductSize
from django.db.models import Q
from wishlist.forms import AddToWishlistForm
from orders.models import OrderItem
from .forms import ProductReviewForm
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from cart.models import Cart, CartItem
import json


class IndexView(TemplateView):
    template_name = 'main/base.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(parent__isnull=True).prefetch_related('subcategories')
        context['current_category'] = None

        # Само outfit-и
        context['male_outfits'] = Outfit.objects.filter(gender='male').order_by('-created_at')[:3]
        context['female_outfits'] = Outfit.objects.filter(gender='female').order_by('-created_at')[:3]

        return context


    
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if request.headers.get('HX-Request'):
            return TemplateResponse(request, 'main/home_content.html', context)
        return TemplateResponse(request, self.template_name, context)
    

class CatalogView(TemplateView):
    template_name = 'main/base.html'

    FILTER_MAPPING = {
        'color': lambda queryset, value: queryset.filter(color__iexact=value),
        'min_price': lambda queryset, value: queryset.filter(price_gte=value),
        'max_price': lambda queryset, value: queryset.filter(price_lte=value),
        'size': lambda queryset, value: queryset.filter(product_sizes__size__name=value),
    }


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_slug = kwargs.get('category_slug')
        categories = Category.objects.filter(parent__isnull=True).prefetch_related('subcategories')
        products = Product.objects.all().order_by('-created_at')
        current_category = None

        if category_slug:
            current_category = get_object_or_404(Category, slug=category_slug)
            products = products.filter(category=current_category)

        query = self.request.GET.get('q')
        if query:
            products = products.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )

        filter_params = {}
        for param, filter_func in self.FILTER_MAPPING.items():
            value = self.request.GET.get(param)
            if value:
                products = filter_func(products, value)
                filter_params[param] = value
            else:
                filter_params[param] = ''

        filter_params['q'] = query or ''

        context.update({
            'categories': categories,
            'products': products,
            'current_category': category_slug,
            'filter_params': filter_params,
            'sizes': Size.objects.all(),
            'search_query': query or ''
        })

        if self.request.GET.get('show_search') == 'true':
            context['show_search'] = True
        elif self.request.GET.get('reset_search') == 'true':
            context['reset_search'] = True
        
        return context
    

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if request.headers.get('HX-Request'):
            if context.get('show_search'):
                return TemplateResponse(request, 'main/search_input.html', context)
            elif context.get('reset_search'):
                return TemplateResponse(request, 'main/search_button.html', {})
            template = 'main/filter_modal.html' if request.GET.get('show_filters') == 'true' else 'main/catalog.html'
            return TemplateResponse(request, template, context)
        return TemplateResponse(request, self.template_name, context)
    

class ProductDetailView(DetailView):
    model = Product
    template_name = 'main/base.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        context['categories'] = Category.objects.filter(parent__isnull=True).prefetch_related('subcategories')
        context['related_products'] = Product.objects.filter(
            category=product.category
        ).exclude(id=product.id)[:4]
        context['current_category'] = product.category.slug
        context['wishlist_form'] = AddToWishlistForm(product=product, user=self.request.user)
        context['reviews'] = product.reviews.all().order_by('-created_at')


        return context
    

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(**kwargs)
        if request.headers.get('HX-Request'):
            return TemplateResponse(request, 'main/product_detail.html', context)
        return TemplateResponse(request, self.template_name, context)
    
@login_required
@csrf_exempt
def submit_review(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)

        # Проверка: потребителят е купувал този продукт
        if not OrderItem.objects.filter(order__user=request.user, product=product).exists():
            return JsonResponse({'error': 'You can only review products you have purchased.'}, status=403)

        form = ProductReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            return JsonResponse({'success': 'Review submitted successfully.'})
        else:
            return JsonResponse({'errors': form.errors}, status=400)
        

@require_GET
def get_outfit_modal(request, outfit_id):
    outfit = get_object_or_404(Outfit, id=outfit_id)
    items = outfit.items.select_related('product')

    product_data = []
    for item in items:
        product = item.product
        sizes = ProductSize.objects.filter(product=product).select_related('size')
        product_data.append({
            'product': product,
            'sizes': sizes
        })

    return render(request, 'main/get_the_look_modal.html', {
        'outfit': outfit,
        'product_data': product_data
    })


@require_POST
def add_outfit_to_cart(request):
    added_count = 0  # ✅ започваме с 0

    try:
        data = json.loads(request.body)
        products = data.get('products', [])

        if not products:
            return JsonResponse({'error': 'No products provided'}, status=400)

        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key

        cart, _ = Cart.objects.get_or_create(session_key=session_key)

        for item in products:
            product_id = item.get('product_id')
            size_id = item.get('size_id')

            if not product_id or not size_id:
                continue

            # Вземаме продукта и размера
            product = Product.objects.get(id=product_id)
            product_size = ProductSize.objects.get(product=product, size_id=size_id)

            # Използваме вградения метод на Cart
            cart.add_product(product, product_size, quantity=1)

            added_count += 1  # ✅ увеличаваме брояча

        return JsonResponse({
            'success': True,
            'cart_count': cart.total_items,
            'added_count': added_count  # ✅ връщаме колко артикула са добавени
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


        