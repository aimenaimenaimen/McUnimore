"""
URL configuration for PROGETTO project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from PROGETTO import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.homepage, name='homepage'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('cart/', views.cart_view, name='cart'),  # Percorso per il carrello
    path('prodotti/', views.prodotti_view, name='prodotti'),
    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove_from_cart/<int:cart_item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('orders/', views.orders_view, name='orders'),
    path('ristoratore/login/', views.ristoratore_login, name='ristoratore_login'),
    path('gestione_ordine/', views.gestione_ordine, name='gestione_ordine'),  # Nuovo percorso per la gestione ordini
    path('update_order_status/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('coupon/', views.coupon_page, name='coupon_page'),
    path('reveal_coupon/<int:coupon_id>/', views.reveal_coupon, name='reveal_coupon'),  # Aggiungi questa linea
    path('apply_coupon/', views.apply_coupon, name='apply_coupon'),
    path('map/', views.map_view, name='map'),  # Aggiungi questa linea
    path('create_order/', views.create_order, name='create_order'),
]


