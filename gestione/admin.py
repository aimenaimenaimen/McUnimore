from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Product, Order, User, FastFood

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('is_ristoratore',)}),  # Aggiungi il campo is_ristoratore
    )
    list_display = UserAdmin.list_display + ('is_ristoratore',)  # Mostra is_ristoratore nella lista utenti

admin.site.register(User, CustomUserAdmin)

admin.site.register(Product)

admin.site.register(FastFood)

class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'total_price', 'status', 'tipo_di_ordine')
    list_filter = ('status', 'tipo_di_ordine', 'created_at')
    search_fields = ('user__username', 'items')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'user', 'total_price', 'items')

    # Rendi il campo `status` modificabile
    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return self.readonly_fields
        return self.readonly_fields + ('status',)

admin.site.register(Order, OrderAdmin)
