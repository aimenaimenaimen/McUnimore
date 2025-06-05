from django.test import TestCase
from django.contrib.auth.models import User

class SimpleTestCase(TestCase):
    def test_homepage(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_404_page(self):
        response = self.client.get('/nonexistent-page/')
        self.assertEqual(response.status_code, 404)

    def test_coupon_page(self):
        # Assumendo che tu abbia una pagina "about" configurata
        response = self.client.get('/register/')
        self.assertEqual(response.status_code, 200)

    def test_login(self):
        # Creazione di un utente di test
        user = User.objects.create_user(username='testuser', password='testpassword')
        
        # Effettua il login
        login = self.client.login(username='testuser', password='testpassword')
        self.assertTrue(login)

        # Verifica che l'utente sia autenticato accedendo a una pagina protetta
        response = self.client.get('/protected-page/')  # Sostituisci con l'URL di una pagina protetta
        self.assertEqual(response.status_code, 200)
