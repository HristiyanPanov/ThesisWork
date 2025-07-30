# wishlist/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse, HttpResponse
from main.models import ProductSize, Product
from .models import WishlistItem
from django.middleware.csrf import get_token
from django.template.loader import render_to_string

def _items(user):
    return (WishlistItem.objects
            .filter(user=user)
            .select_related("product", "product_size", "product_size__size"))

def _count(user):
    return WishlistItem.objects.filter(user=user).count()


@login_required
@require_POST
def add_to_wishlist(request, product_id):
    size_id = request.POST.get("size_id")
    if not size_id:
        return JsonResponse({"success": False, "error": "Size is required"}, status=400)

    try:
        ps = ProductSize.objects.get(id=size_id, product_id=product_id)
    except ProductSize.DoesNotExist:
        return JsonResponse({"success": False, "error": "Invalid size"}, status=400)

    item, created = WishlistItem.objects.get_or_create(
        user=request.user,
        product=ps.product,
        product_size=ps
    )

    message = (
        f"{ps.product.name} added to wishlist"
        if created else
        f"{ps.product.name} is already in your wishlist"
    )

    return JsonResponse({
        "success": True,
        "created": created,
        "count": _count(request.user),
        "message": message
    })


@login_required
@require_POST
def remove_from_wishlist(request, item_id):
    item = get_object_or_404(WishlistItem, id=item_id, user=request.user)
    item.delete()

    if request.headers.get("HX-Request"):
        items = _items(request.user)
        return render(request, "wishlist/wishlist_modal.html", {
            "items": items,
            "wishlist_count": items.count()
        })

    return JsonResponse({"success": True, "count": _count(request.user)})


@login_required
@require_GET
def wishlist_modal(request):
    items = _items(request.user)
    return render(request, "wishlist/wishlist_modal.html", {
        "items": items,
        "wishlist_count": items.count(),
        "csrf_token": get_token(request),  # <-- това е ключово
    })

@login_required
@require_GET
def wishlist_count(request):
    return JsonResponse({"count": _count(request.user)})

@login_required
@require_POST
def clear_wishlist(request):
    WishlistItem.objects.filter(user=request.user).delete()

    return render(request, "wishlist/wishlist_modal.html", {
        "items": [],
        "wishlist_count": 0
    })

@login_required
@require_GET
def wishlist_notification(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, "wishlist/wishlist_notification.html", {"product": product})

