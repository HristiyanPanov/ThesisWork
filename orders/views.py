from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponse, JsonResponse
from django.template.response import TemplateResponse
from django.views.generic import View
from .forms import OrderForm
from .models import Order, OrderItem
from cart.views import CartMixin
from cart.models import Cart
from main.models import ProductSize, NewsletterSubscriber
from django.shortcuts import get_object_or_404
from payment.views import create_stripe_checkout_session
from decimal import Decimal
import logging
from django.views.decorators.csrf import csrf_exempt
import json


logger = logging.getLogger(__name__)


@method_decorator(login_required(login_url='/users/login'), name='dispatch')
class CheckoutView(CartMixin, View):
    def get(self, request):
        cart = self.get_cart(request)
        logger.debug(f"Checkout view: session_key={request.session.session_key}, cart_id={cart.id}, total_items={cart.total_items}, subtotal={cart.subtotal}")

        if cart.total_items == 0:
            logger.warning("Cart is empty, redirecting to cart page")
            if request.headers.get('HX-Request'):
                return TemplateResponse(request, 'orders/empty_cart.html', {'message': 'Your cart is empty'})
            return redirect('cart:cart_modal')
        

        total_price = cart.subtotal
        logger.debug(f"Total price: {total_price}")

        form = OrderForm(user=request.user)
        context = {
            'form': form,
            'cart': cart,
            'cart_items': cart.items.select_related('product', 'product_size__size').order_by('-added_at'),
            'total_price': total_price,
        }

        if request.headers.get('HX-Request'):
            return TemplateResponse(request, 'orders/checkout_content.html', context)
        return render(request, 'orders/checkout.html', context)
    

    def post(self, request):
        cart = self.get_cart(request)
        payment_provider = request.POST.get('payment_provider')
        logger.debug(f"Checkout POST: session_key={request.session.session_key}, cart_id={cart.id}, total_items={cart.total_items}, payment_provider={payment_provider}")

        if cart.total_items == 0:
            logger.warning("Cart is empty, redirecting to cart page")
            if request.headers.get('HX-Request'):
                return TemplateResponse(request, 'orders/empty_cart.html', {'message': 'Your cart is empty'})
            return redirect('cart:cart_modal')
        
        if not payment_provider or payment_provider not in ['stripe', 'heleket']:
            logger.error(f"Invalid or missing payment provider: {payment_provider}")
            context = {
                'form': OrderForm(user=request.user),
                'cart': cart,
                'cart_items': cart.items.select_related('product', 'product_size__size').order_by('-added_at'),
                'total_price': cart.subtotal,
                'error_message': 'Please select valid payment provider (Stripe or Heleket).',
            }
            if request.headers.get('HX-Request'):
                return TemplateResponse(request, 'orders/checkout_content.html', context)
            return render(request, 'orders/checkout.html', context)
        
        # Изчисляване на subtotal и отстъпка
        subtotal = cart.subtotal
        discount_code = request.POST.get('discount_code', '').strip()
        discount_percent = 0

        if discount_code:
            code_raw = discount_code
            exists = NewsletterSubscriber.objects.filter(discount_code__iexact=code_raw).exists()
            if exists:
                discount_percent = 10

        discount_value = subtotal * (Decimal(discount_percent) / Decimal('100'))
        total_price = subtotal - discount_value

        form_data = request.POST.copy()
        if not form_data.get('email'):
            form_data['email'] = request.user.email
        form = OrderForm(form_data, user=request.user)

        if form.is_valid():
            order = Order.objects.create(
                user=request.user,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                email=form.cleaned_data['email'],
                company=form.cleaned_data['company'],
                address1=form.cleaned_data['address1'],
                address2=form.cleaned_data['address2'],
                city=form.cleaned_data['city'],
                country=form.cleaned_data['country'],
                province=form.cleaned_data['province'],
                postal_code=form.cleaned_data['postal_code'],
                phone=form.cleaned_data['phone'],
                special_instructions='',
                total_price=total_price,
                payment_provider=payment_provider,
                discount=discount_value,
            )

            for item in cart.items.select_related('product', 'product_size'):
                logger.debug(f"Processing cart item: product={item.product.name}, size={item.product_size.size.name}, quantity={item.quantity}")
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    size=item.product_size,
                    quantity=item.quantity,
                    price=item.product.price or Decimal('0.00')
                )

            try:
                logger.info(f"Creating payment session for provider: {payment_provider}")
                if payment_provider == 'stripe':
                    logger.debug("Creating Stripe checkout session")
                    checkout_session =  create_stripe_checkout_session(order, request)
                    cart.clear()
                    if request.headers.get('HX-Request'):
                        response = HttpResponse(status=200)
                        response['HX-Redirect'] = checkout_session.url
                        logger.info(f"HX-Redirect to Stripe: {checkout_session.url}")
                        return response
                    return redirect(checkout_session.url)
                
            except Exception as e:
                logger.error(f"Error creating payment: {str(e)}", exc_info=True)
                order.delete()
                context = {
                    'form': form,
                    'cart': cart,
                    'cart_items': cart.items.select_related('product', 'product_size__size').order_by('-added_at'),
                    'total_price': total_price,
                    'error_message': f'Payment processing error: {str(e)}',
                }
                if request.headers.get('HX-Request'):
                    return TemplateResponse(request, 'orders/checkout_content.html', context)
                return render(request, 'orders/checkout.html', context)
            
        else:
            logger.warning(f"Form validation error: {form.errors}")
            context = {
                'form': form,
                'cart': cart,
                'cart_items': cart.items.select_related('product', 'product_size__size').order_by('-added_at'),
                'total_price': total_price,
                'error_message': f'Please correct the errors in the form.',
            }
            if request.headers.get('HX-Request'):
                return TemplateResponse(request, 'orders/checkout_content.html', context)
            return render(request, 'orders/checkout.html', context)
        

@csrf_exempt
def validate_discount_code(request):
    if request.method != 'POST':
        return JsonResponse({'valid': False})

    try:
        data = json.loads(request.body or '{}')
        code_raw = (data.get('code') or '').strip()

        # нормализирай subtotal: махни валутни символи, замени запетая с точка
        raw_subtotal = str(data.get('subtotal', 0))
        cleaned = ''.join(ch for ch in raw_subtotal if (ch.isdigit() or ch in '.,-'))
        cleaned = cleaned.replace(',', '.')
        try:
            subtotal = float(cleaned)
        except ValueError:
            subtotal = 0.0

        # case-insensitive валидиране на кода
        valid = (
            NewsletterSubscriber.objects.filter(discount_code__iexact=code_raw).exists()
        )

        if not valid:
            return JsonResponse({'valid': False})

        discount_value = round(subtotal * 0.10, 2)
        return JsonResponse({'valid': True, 'discount_value': discount_value})

    except Exception as e:
        return JsonResponse({'valid': False, 'error': str(e)})
