from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from .models import FastFood

User = get_user_model()

class SiteTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        FastFood.objects.create(nome='McTest', indirizzo='Via Test 1', latitudine=45.0, longitudine=9.0)

    def test_register(self):
        response = self.client.post('/register/', {
            'username': 'newuser',
            'password1': 'newpass123',
            'password2': 'newpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect dopo registrazione
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_login(self):
        response = self.client.post('/login/', {
            'username': 'testuser',
            'password': 'testpass'
        })
        self.assertEqual(response.status_code, 302)  # Redirect dopo login

    def test_homepage_access(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Fast Food")  # Modifica secondo il contenuto reale

    def test_fastfood_on_map(self):
        response = self.client.get('/mappa/')  # Modifica secondo la tua url
        self.assertContains(response, 'McTest')
        self.assertContains(response, 'Via Test 1')
