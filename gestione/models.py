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
    is_ristoratore = models.BooleanField(default=False)  # Flag per identificare i ristoratori
    revealed_coupons = models.ManyToManyField('Coupon', blank=True, related_name='revealed_by_users')  # Cambia il related_name

class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image_name = models.CharField(max_length=255, blank=True, null=True)  # Nome dell'immagine PNG

    def __str__(self):
        return self.name

class Coupon(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='owned_coupons', null=True, blank=True)
    code = models.CharField(max_length=50, unique=True)  # Codice univoco del coupon
    discount = models.IntegerField()  # Percentuale di sconto
    description = models.CharField(max_length=255)  # Descrizione del coupon
    is_active = models.BooleanField(default=True)  # Stato del coupon (attivo o meno)

    def __str__(self):
        return f"{self.code} - {self.discount}%"
    
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
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    latitudine = models.FloatField()
    longitudine = models.FloatField()

    def __str__(self):
        return self.name
    
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


