from django.test import TestCase, Client  # Importa TestCase per i test e Client per simulare richieste HTTP
from django.contrib.auth import get_user_model  # Importa la funzione per ottenere il modello utente personalizzato
from .models import FastFood, Coupon  # Importa i modelli FastFood e Coupon

User = get_user_model()  # Ottiene il modello utente personalizzato (User)

class SiteTests(TestCase):
    """
    Classe che contiene i test automatici per il sito.
    """

    def setUp(self):
        """
        Metodo eseguito prima di ogni test.
        Crea un client di test, un utente di test, un fast food di test e 10 coupon liberi.
        """
        self.client = Client()  # Crea un client per simulare richieste HTTP
        self.user = User.objects.create_user(username='testuser', password='testpass')  # Crea un utente di test
        # Crea un fast food di test con nome, indirizzo e coordinate
        FastFood.objects.create(nome='McTest', indirizzo='Via Test 1', latitudine=45.0, longitudine=9.0)
        # Crea 10 coupon senza utente associato (liberi)
        for i in range(10):
            Coupon.objects.create(
                user=None,
                code=f"CODE{i}",
                discount=10,
                description="Test coupon",
                is_active=True
            )

    def test_register(self):
        """
        Testa la registrazione di un nuovo utente.
        Invia una POST a /register/ e verifica che l'utente venga creato e che ci sia un redirect.
        """
        response = self.client.post('/register/', {
            'username': 'newuser',
            'password1': 'newpass123',
            'password2': 'newpass123'
        })
        self.assertEqual(response.status_code, 302)  # Verifica che ci sia un redirect dopo la registrazione
        self.assertTrue(User.objects.filter(username='newuser').exists())  # Verifica che l'utente sia stato creato

    def test_login(self):
        """
        Testa il login di un utente esistente.
        Invia una POST a /login/ e verifica che ci sia un redirect.
        """
        response = self.client.post('/login/', {
            'username': 'testuser',
            'password': 'testpass'
        })
        self.assertEqual(response.status_code, 302)  # Verifica che ci sia un redirect dopo il login

    def test_homepage_access(self):
        """
        Testa che la homepage sia accessibile (status code 200).
        """
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)  # Verifica che la homepage sia accessibile

    def test_fastfood_on_map(self):
        """
        Testa che il fast food di test sia presente nella pagina della mappa.
        Verifica che il nome e l'indirizzo compaiano nella risposta.
        """
        response = self.client.get('/map/')
        self.assertContains(response, 'McTest')  # Verifica che il nome sia presente
        self.assertContains(response, 'Via Test 1')  # Verifica che l'indirizzo sia presente

    def test_coupon_assignment_on_registration(self):
        """
        Testa che, dopo la registrazione di un nuovo utente, gli vengano assegnati 5 coupon.
        """
        response = self.client.post('/register/', {
            'username': 'couponuser',
            'password1': 'couponpass123',
            'password2': 'couponpass123'
        })
        user = User.objects.get(username='couponuser')  # Recupera il nuovo utente
        assigned_coupons = Coupon.objects.filter(user=user)  # Recupera i coupon assegnati a quell'utente
        self.assertEqual(assigned_coupons.count(), 5)  # Verifica che siano esattamente 5

    def test_coupon_not_assigned_twice(self):
        """
        Testa che i coupon non vengano assegnati a più utenti.
        Registra due utenti e verifica che non abbiano coupon in comune.
        """
        self.client.post('/register/', {
            'username': 'user1',
            'password1': 'pass12345',
            'password2': 'pass12345'
        })
        self.client.post('/register/', {
            'username': 'user2',
            'password1': 'pass12345',
            'password2': 'pass12345'
        })
        user1 = User.objects.get(username='user1')
        user2 = User.objects.get(username='user2')
        coupons1 = set(Coupon.objects.filter(user=user1).values_list('code', flat=True))
        coupons2 = set(Coupon.objects.filter(user=user2).values_list('code', flat=True))
        self.assertTrue(coupons1.isdisjoint(coupons2))  # Verifica che non ci siano coupon in comune

    def test_coupon_unique_code(self):
        """
        Testa che tutti i codici coupon siano unici nel database.
        """
        codes = Coupon.objects.values_list('code', flat=True)
        self.assertEqual(len(codes), len(set(codes)))  # Verifica che non ci siano duplicati

   