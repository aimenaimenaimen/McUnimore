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
    if not request.user.is_authenticated:
        return redirect('login')  # Reindirizza al login se non autenticato

    cart = Cart.objects.get(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)
    total_price = sum(item.product.price * item.quantity for item in cart_items)

    if cart.coupon:
        discount = (total_price * cart.coupon.discount) / 100
        total_price -= discount

    if request.method == 'POST':
        order_type = request.POST.get('order_type')
        fast_food_id = request.POST.get('fast_food')
        address = request.POST.get('address')
        city = request.POST.get('city')

        # Validazione
        if order_type == 'delivery' and (not address or not city):
            messages.error(request, "Indirizzo e città sono obbligatori per la consegna.")
            return redirect('cart')

        fast_food = FastFood.objects.get(id=fast_food_id) if fast_food_id else None

        # Creazione ordine
        order = Order.objects.create(
            user=request.user,
            cart=cart,
            order_type=order_type,
            fast_food=fast_food,
            address=address,
            city=city,
            total_price=total_price
        )
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
    if not request.user.is_authenticated or not request.user.is_ristoratore:
        return redirect('ristoratore_login')  # Reindirizza al login se non autenticato o non autorizzato

    fast_foods = FastFood.objects.all()  # Recupera tutti i fast-food
    selected_fast_food = request.GET.get('fast_food')  # Recupera il fast-food selezionato
    orders = Order.objects.filter(fast_food_id=selected_fast_food) if selected_fast_food else []

    fast_food_id = request.GET.get('fast_food')  # Ottieni l'ID del fast food selezionato
    fast_food_name = None

    if fast_food_id:
        fast_food = next((ff for ff in fast_foods if ff.id == int(fast_food_id)), None)
        fast_food_name = fast_food.name if fast_food else None

    context = {
        'fast_foods': fast_foods,  # Lista di fast food
        'orders': orders,          # Lista di ordini
        'selected_fast_food': fast_food_name,  # Nome del fast food selezionato
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

def update_order_status(request, order_id):
    if not request.user.is_authenticated or not request.user.is_ristoratore:
        return redirect('ristoratore_login')  # Reindirizza al login se non autenticato o non autorizzato

    if request.method == 'POST':
        status = request.POST.get('status')
        order = Order.objects.get(id=order_id)
        order.status = status
        order.save()
        return redirect('gestione_ordine')  # Reindirizza alla pagina di gestione ordini

@login_required
def coupon_page(request):
    # Seleziona 5 coupon casuali attivi
    coupons = list(Coupon.objects.filter(is_active=True))
    random_coupons = random.sample(coupons, min(len(coupons), 5))

    # Aggiungi informazione sui coupon rivelati dall'utente
    revealed_coupons = request.user.revealed_coupons.all()

    context = {
        'coupons': random_coupons,
        'revealed_coupons': revealed_coupons,
    }
    return render(request, 'coupon_page.html', context)

def apply_coupon(request):
    if request.method == 'POST':
        coupon_code = request.POST.get('coupon_code')
        coupon = get_object_or_404(Coupon, code=coupon_code, is_active=True)
        cart = Cart.objects.get(user=request.user)
        cart.coupon = coupon
        cart.save()
        return redirect('cart')  # Reindirizza al carrello

@csrf_exempt
@login_required
def reveal_coupon(request, coupon_id):
    if request.method == 'POST':
        coupon = Coupon.objects.get(id=coupon_id)
        coupon.revealed_by.add(request.user)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)