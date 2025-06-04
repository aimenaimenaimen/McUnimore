from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.contrib import messages
from gestione.models import User, Cart, Product, CartItem, Order, FastFood  # Usa un'importazione assoluta
import pytz

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

        if user:
            login(request, user)
            return redirect('homepage')  # Reindirizza alla homepage dopo il login
        else:
            return render(request, 'login.html', {'error': 'Credenziali non valide.'})

    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('homepage')

def cart_view(request):
    if not request.user.is_authenticated:
        return redirect('login')  # Reindirizza al login se non autenticato

    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.cartitem_set.all()
    total_price = sum(item.quantity * item.product.price for item in cart_items)  # Calcola il prezzo totale
    fast_foods = FastFood.objects.all()  # Recupera tutti i fast-food dal database

    if request.method == 'POST' and 'place_order' in request.POST:
        tipo_di_ordine = request.POST.get('tipo_di_ordine', 'DELIVERY')
        if tipo_di_ordine == 'DELIVERY':
            delivery_address = request.POST.get('delivery_address')
            delivery_city = request.POST.get('delivery_city')

            # Validazione lato server
            if not delivery_address or not delivery_city:
                messages.error(request, 'Per gli ordini Delivery, i campi Indirizzo e Città sono obbligatori.')
                return render(request, 'cart.html', {'cart_items': cart_items, 'total_price': total_price, 'fast_foods': fast_foods})

            delivery_fast_food_id = request.POST.get('delivery_fast_food')
            delivery_fast_food = FastFood.objects.get(id=delivery_fast_food_id)
            items_details = "\n".join([f"{item.product.name} x {item.quantity}" for item in cart_items])
            Order.objects.create(
                user=request.user,
                total_price=total_price,
                items=items_details,
                tipo_di_ordine=tipo_di_ordine,
                delivery_address=delivery_address,
                delivery_city=delivery_city,
                fast_food=delivery_fast_food,
                status='ORDINE RICEVUTO'
            )
        elif tipo_di_ordine == 'IN LOCO':
            fast_food_id = request.POST.get('fast_food')
            fast_food = FastFood.objects.get(id=fast_food_id)
            items_details = "\n".join([f"{item.product.name} x {item.quantity}" for item in cart_items])
            Order.objects.create(
                user=request.user,
                total_price=total_price,
                items=items_details,
                tipo_di_ordine=tipo_di_ordine,
                fast_food=fast_food,
                status='ORDINE RICEVUTO'
            )
        cart_items.delete()  # Svuota il carrello
        return redirect('orders')  # Reindirizza alla pagina degli ordini

    return render(request, 'cart.html', {'cart_items': cart_items, 'total_price': total_price, 'fast_foods': fast_foods})

def prodotti_view(request):
    products = Product.objects.all()

    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        product = Product.objects.get(id=product_id)

        # Recupera o crea il carrello per l'utente
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

        if created:
            cart_item.quantity = 1  # Imposta la quantità iniziale a 1
        else:
            cart_item.quantity += 1  # Incrementa la quantità se l'elemento esiste già

        cart_item.save()

        # Passa il messaggio al template
        return render(request, 'prodotti.html', {'products': products, 'message': 'Prodotto aggiunto al carrello correttamente!'})

    return render(request, 'prodotti.html', {'products': products})

def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        return redirect('login')  # Reindirizza al login se non autenticato

    try:
        product = Product.objects.get(id=product_id)
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, item=product)
        cart_item.quantity += 1
        cart_item.save()

        return redirect('cart')  # Reindirizza al carrello dopo l'aggiunta
    except Product.DoesNotExist:
        return redirect('prodotti')  # Reindirizza alla pagina dei prodotti se il prodotto non esiste

def remove_from_cart(request, cart_item_id):
    if not request.user.is_authenticated:
        return redirect('login')  # Reindirizza al login se non autenticato

    cart_item = get_object_or_404(CartItem, id=cart_item_id, cart__user=request.user)
    cart_item.delete()  # Rimuove l'elemento dal carrello

    return redirect('cart')  # Reindirizza al carrello

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

    return render(request, 'gestione_ordine.html', {'fast_foods': fast_foods, 'orders': orders})

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