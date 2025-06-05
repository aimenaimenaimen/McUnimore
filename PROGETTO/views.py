from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from gestione.models import Product, Cart, CartItem
from gestione.models import User, Order, FastFood, Coupon  # Usa un'importazione assoluta
import pytz
import random
from django.views.decorators.csrf import csrf_exempt
from django.db.models.signals import post_save
from django.dispatch import receiver

def homepage(request):
    return render(request, 'homepage.html')

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Salva i dati nel database con password hashata
        user = User(username=username)
        user.set_password(password)  # Hasha la password
        user.save()

        # Autentica e logga l'utente
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)

        return redirect('homepage')

    return render(request, 'register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'homepage')  # Reindirizza alla pagina richiesta o alla homepage
            return redirect(next_url)
        else:
            return render(request, 'login.html', {'error': 'Credenziali non valide'})

    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('homepage')

def cart_view(request):
    cart = Cart.objects.get(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)
    total_price = sum(item.product.price * item.quantity for item in cart_items)

    if cart.coupon:
        discount = (total_price * cart.coupon.discount) / 100
        total_price -= discount

    if request.method == 'POST':
        order_type = request.POST.get('order_type')
        address = request.POST.get('address')
        city = request.POST.get('city')
        fast_food_id = request.POST.get('fast_food')

        # Validazione per il tipo di ordine "Delivery"
        if order_type == 'delivery':
            if not address or not city:
                messages.error(request, "Indirizzo e città sono obbligatori per la consegna.")
                return redirect('cart')

        # Validazione per il fast-food
        if not fast_food_id:
            messages.error(request, "Seleziona un fast-food.")
            return redirect('cart')

        fast_food = FastFood.objects.get(id=fast_food_id) if fast_food_id else None

        # Creazione ordine
        order = Order.objects.create(
            user=request.user,
            total_price=total_price,
            items=", ".join([f"{item.quantity}x {item.product.name}" for item in cart_items]),
            tipo_di_ordine=order_type,
            fast_food=fast_food,
            delivery_address=address if order_type == 'delivery' else None,
            delivery_city=city if order_type == 'delivery' else None
        )

        # Svuota il carrello
        cart_items.delete()
        cart.total_price = 0
        cart.coupon = None
        cart.save()

        messages.success(request, "Ordine effettuato con successo!")
        return redirect('orders')

    fast_foods = FastFood.objects.all()
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'fast_foods': fast_foods,
    }
    return render(request, 'cart.html', context)

@login_required
def prodotti_view(request):
    products = Product.objects.all()
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        product = get_object_or_404(Product, id=product_id)
        cart, created = Cart.objects.get_or_create(user=request.user)
        # Aggiungi il prodotto al carrello (puoi usare una relazione ManyToMany o un altro modello)
        cart.total_price += product.price  # Aggiorna il prezzo totale
        cart.save()
        return redirect('prodotti')  # Ricarica la pagina dei prodotti
    return render(request, 'prodotti.html', {'products': products})

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)

    # Controlla se il prodotto è già nel carrello
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not item_created:
        cart_item.quantity += 1  # Incrementa la quantità se il prodotto è già presente
    cart_item.save()

    # Aggiorna il prezzo totale del carrello
    cart.total_price += product.price
    cart.save()

    # Aggiungi un messaggio di conferma
    messages.success(request, f"Il prodotto '{product.name}' è stato aggiunto al carrello!")

    return redirect('prodotti')  # Reindirizza alla pagina dei prodotti

@login_required
def remove_from_cart(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id, cart__user=request.user)
    cart_item.cart.total_price -= cart_item.product.price * cart_item.quantity
    cart_item.cart.save()
    cart_item.delete()
    messages.success(request, f"Il prodotto '{cart_item.product.name}' è stato rimosso dal carrello.")
    return redirect('cart')

def orders_view(request):
    if not request.user.is_authenticated:
        return redirect('login')  # Reindirizza al login se non autenticato

    # Recupera gli ordini dell'utente
    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    # Converte l'orario in UTC+2
    timezone_utc2 = pytz.timezone('Europe/Rome')
    for order in orders:
        order.created_at = order.created_at.astimezone(timezone_utc2)

    return render(request, 'orders.html', {'orders': orders})

def gestione_ordine(request):
    fast_foods = FastFood.objects.all()
    selected_fast_food = None
    orders = []

    if 'fast_food' in request.GET:
        fast_food_id = request.GET.get('fast_food')
        selected_fast_food = get_object_or_404(FastFood, id=fast_food_id)
        orders = Order.objects.filter(fast_food=selected_fast_food).order_by('-created_at')

    context = {
        'fast_foods': fast_foods,
        'selected_fast_food': selected_fast_food.name if selected_fast_food else "Tutti",
        'orders': orders,
    }
    return render(request, 'gestione_ordine.html', context)

def ristoratore_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user and user.is_ristoratore:  # Verifica che l'utente sia un ristoratore
            login(request, user)
            return redirect('gestione_ordine')  # Reindirizza alla gestione ordini
        else:
            return render(request, 'ristoratore_login.html', {'error': 'Credenziali non valide o utente non autorizzato.'})

    return render(request, 'ristoratore_login.html')

@login_required
def update_order_status(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        order.status = new_status
        order.save()
        messages.success(request, f"Lo stato dell'ordine è stato aggiornato a '{new_status}'.")
        return redirect('gestione_ordine')  # Reindirizza alla pagina di gestione ordini

@login_required
def coupon_page(request):
    cart = Cart.objects.get(user=request.user)
    # Filtra solo i coupon attivi e non applicati
    revealed_coupons = request.user.revealed_coupons.filter(is_active=True).exclude(id=cart.coupon.id if cart.coupon else None)

    context = {
        'revealed_coupons': revealed_coupons,
    }
    return render(request, 'coupon_page.html', context)

@login_required
def apply_coupon(request):
    if request.method == 'POST':
        cart = Cart.objects.get(user=request.user)
        if cart.coupon:
            messages.error(request, "Hai già applicato un coupon.")
            return redirect('cart')

        coupon_code = request.POST.get('coupon_code')
        try:
            coupon = Coupon.objects.get(code=coupon_code, is_active=True)
            cart.coupon = coupon
            cart.save()

            # Disattiva il coupon
            coupon.is_active = False
            coupon.save()

            messages.success(request, f"Coupon '{coupon_code}' accettato! Sconto del {coupon.discount}% applicato.")
        except Coupon.DoesNotExist:
            messages.error(request, "Il coupon inserito non è valido o è scaduto.")
        return redirect('cart')

@csrf_exempt
@login_required
def reveal_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id, is_active=True)
    request.user.revealed_coupons.add(coupon)  # Assumi che ci sia una relazione ManyToMany tra User e Coupon
    messages.success(request, f"Hai rivelato il coupon: {coupon.code}")
    return redirect('coupon_page')

@receiver(post_save, sender=User)
def assign_coupons_to_user(sender, instance, created, **kwargs):
    if created:  # Esegui solo quando l'utente viene creato
        coupons = Coupon.objects.filter(is_active=True)[:5]  # Prendi i primi 5 coupon attivi
        num_coupons = random.randint(3, 5)  # Numero casuale tra 3 e 5
        for coupon in random.sample(list(coupons), min(num_coupons, len(coupons))):
            instance.revealed_coupons.add(coupon)
