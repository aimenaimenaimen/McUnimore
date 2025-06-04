import random
import string
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission, User
from django.conf import settings


class BaseModel(models.Model):

    class Meta:
        abstract = True  # specify this model as an Abstract Model
        app_label = 'wdland'
# Create your models here.
class User(AbstractUser):
    is_ristoratore = models.BooleanField(default=False)  # Flag per identificare i ristoratori, di default False

class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image_name = models.CharField(max_length=255, blank=True, null=True)  # Nome dell'immagine PNG

    def __str__(self):
        return self.name

class Coupon(models.Model):
    code = models.CharField(max_length=8, unique=True)
    discount = models.IntegerField()  # Percentuale di sconto come numero intero
    description = models.TextField(blank=True, null=True)  # Descrizione del coupon
    is_active = models.BooleanField(default=True)
    revealed_by = models.ManyToManyField(User, related_name='revealed_coupons', blank=True)

    @staticmethod
    def generate_random_code():
        import random
        return ''.join(random.choices('0123456789', k=8))  # Genera un codice di 8 cifre numeriche

    def __str__(self):
        return self.code
    
class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    products = models.ManyToManyField(Product, blank=True)  # Relazione ManyToMany con i prodotti

    def calculate_discounted_price(self):
        if self.coupon:
            discount = (self.total_price * self.coupon.discount) / 100
            return self.total_price - discount
        return self.total_price

    def __str__(self):
        return f"Carrello di {self.user.username}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)  # Relazione con il carrello
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # Relazione con il prodotto
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} nel carrello di {self.cart.user.username}"

class FastFood(models.Model):
    name = models.CharField(max_length=255)  # Nome del fast-food
    address = models.CharField(max_length=255)  # Indirizzo del fast-food
    city = models.CharField(max_length=100)  # Città
    postal_code = models.CharField(max_length=10)  # Codice postale
    manager = models.ForeignKey(User, on_delete=models.CASCADE, related_name="managed_fast_foods")  # Ristoratore responsabile

    def __str__(self):
        return f"{self.name} - {self.address}, {self.city} ({self.postal_code})"
    
class Order(models.Model):
    STATUS_CHOICES = [
        ('ORDINE RICEVUTO', 'Ordine Ricevuto'),
        ('IN PREPARAZIONE', 'In Preparazione'),
        ('IN CONSEGNA', 'In Consegna'),
        ('CONSEGNATO', 'Consegnato'),
    ]

    ORDER_TYPE_CHOICES = [
        ('DELIVERY', 'Delivery'),
        ('IN LOCO', 'In Loco'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    items = models.TextField()  # Salva i dettagli degli articoli come stringa
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ORDINE RICEVUTO')
    tipo_di_ordine = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES, default='DELIVERY')
    fast_food = models.ForeignKey(FastFood, on_delete=models.SET_NULL, null=True, blank=True)  # Fast-food per "In Loco"
    delivery_address = models.CharField(max_length=255, blank=True, null=True)  # Indirizzo per "Delivery"
    delivery_city = models.CharField(max_length=100, blank=True, null=True)  # Città per "Delivery"

    def __str__(self):
        return f"Ordine di {self.user.username} - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')} - Stato: {self.status} - Tipo: {self.tipo_di_ordine}"


