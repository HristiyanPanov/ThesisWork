from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import HttpResponse
from django.template.response import TemplateResponse
from .forms import CustomUserCreationForm, CustomUserLoginForm, \
    CustomUserUpdateForm
from .models import CustomUser
from django.contrib import messages
from main.models import Product, ProductReview, Category
from orders.models import Order
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .forms import PasswordResetRequestForm
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from .forms import SetNewPasswordForm



def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('main:index')
    else:
        form = CustomUserCreationForm()

    if request.headers.get("HX-Request"):
        return render(request, "users/partials/register_form.html", {"form": form})
    return render(request, "users/register.html", {"form": form})


def login_view(request):
    form = CustomUserLoginForm(request=request, data=request.POST if request.method == 'POST' else None)

    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        next_url = request.GET.get('next') or reverse('main:index')
        if request.headers.get("HX-Request"):
            return HttpResponse(headers={'HX-Redirect': next_url})
        return redirect(next_url)

    if request.headers.get("HX-Request"):
        return render(request, "users/partials/login_form.html", {"form": form})
    return render(request, "users/login.html", {"form": form})


def password_reset_request(request):
    if request.method == "POST":
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            try:
                user = CustomUser.objects.get(email=email)
                subject = f"{settings.EMAIL_SUBJECT_PREFIX}Password Reset Requested"
                context = {
                    "user": user,
                    "domain": request.get_host(),
                    "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                    "token": default_token_generator.make_token(user),
                }
                message = render_to_string("users/password_reset_email.html", context)
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
                messages.success(request, "Email sent with password reset instructions.")
                return redirect("users:password_reset_request")
            except CustomUser.DoesNotExist:
                messages.error(request, "No account found with that email.")
    else:
        form = PasswordResetRequestForm()
    if request.headers.get("HX-Request"):
        return render(request, "users/partials/password_reset_form.html", {"form": form})
    return render(request, "users/password_reset_form.html", {"form": form})


def password_reset_confirm(request, uidb64, token):
    User = get_user_model()
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            form = SetNewPasswordForm(request.POST)
            if form.is_valid():
                user.password = make_password(form.cleaned_data["new_password1"])
                user.save()
                messages.success(request, "Your password has been reset. You can now log in.")
                return redirect("users:login")
        else:
            form = SetNewPasswordForm()
        return render(request, "users/password_reset_confirm.html", {"form": form})
    else:
        messages.error(request, "The password reset link is invalid or has expired.")
        return redirect("users:password_reset_request")    

@login_required(login_url='/users/login')
def profile_view(request):
    if request.method == 'POST':
        form = CustomUserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            if request.headers.get("HX-Request"):
                return HttpResponse(headers={'HX-Redirect': reverse('users:profile')})
            return redirect('users:profile')
    else:
        form = CustomUserUpdateForm(instance=request.user)

    recommended_products = Product.objects.all().order_by('id')[:3]
    latest_order = (
        Order.objects
        .filter(user=request.user)
        .order_by('-created_at')
        .prefetch_related('items__product', 'items__size')
        .first()
    )

    context = {
        'form': form,
        'user': request.user,
        'recommended_products': recommended_products,
        'latest_order': latest_order,
        # нужно е за хедъра в base.html
        'categories': Category.objects.filter(parent__isnull=True).prefetch_related('subcategories'),
    }

    # HTMX → само съдържанието
    if request.headers.get('HX-Request') == 'true':
        return TemplateResponse(request, 'users/partials/profile_content.html', context)

    # Пълен reload / F5 → base + кой partial да вкараме
    context['initial_content_template'] = 'users/partials/profile_content.html'
    return TemplateResponse(request, 'main/base.html', context)



@login_required(login_url='/users/login')
def account_details(request):
    user = CustomUser.objects.get(id=request.user.id)
    return TemplateResponse(request, 'users/partials/account_details.html', {'user': user})


@login_required(login_url='/users/login')
def edit_account_details(request):
    form = CustomUserUpdateForm(instance=request.user)
    return TemplateResponse(request, 'users/partials/edit_account_details.html',
                            {'user': request.user, 'form': form})


@login_required(login_url='/users/login')
def update_account_details(request):
    if request.method == 'POST':
        form = CustomUserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            user.clean()
            user.save()
            updated_user = CustomUser.objects.get(id=user.id)
            request.user = updated_user
            if request.headers.get('HX-Request'):
                return TemplateResponse(request, 'users/partials/account_details.html', {'user': updated_user})
            return TemplateResponse(request, 'users/partials/account_details.html', {'user': updated_user})
        else:
            return TemplateResponse(request, 'users/partials/edit_account_details.html', {'user': request.user, 'form': form})
    if request.headers.get('HX-Request'):
        return HttpResponse(headers={'HX-Redirect': reverse('user:profile')})
    return redirect('users:profile')


def logout_view(request):
    logout(request)
    if request.headers.get('HX-Request'):
        return HttpResponse(headers={'HX-Redirect': reverse('main:index')})
    return redirect('main:index')

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    ctx = {"orders": orders}

    if request.headers.get("HX-Request") == "true":
        return render(request, "users/partials/order_history.html", ctx)

    return render(request, "users/order_history.html", ctx)



@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related('items__product'), id=order_id, user=request.user)
    user_reviews_by_product = {r.product_id: r for r in ProductReview.objects.filter(user=request.user, product__in=[i.product for i in order.items.all()])}
    reviewed_product_ids = list(user_reviews_by_product.keys())

    ctx = {
        "order": order,
        "user_reviews_by_product": user_reviews_by_product,
        "reviewed_product_ids": reviewed_product_ids
    }

    if request.headers.get("HX-Request") == "true":
        return render(request, "users/partials/order_detail.html", ctx)

    return render(request, "users/order_detail.html", ctx)
