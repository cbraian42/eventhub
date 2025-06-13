from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from app.models import Event, User, Location

class EventStatusIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.organizer = User.objects.create_user(
            username='organizador', password='organizador1234', is_organizer=True
        )
        self.location = Location.objects.create(
            name="Prueba",
            address="calle prueba",
            city="Ciudad prueba",
            capacity=100,
            contact="123456"
        )
        self.event = Event.objects.create(
            title="Evento de integración",
            description="Descripción",
            scheduled_at=timezone.now() + timezone.timedelta(days=2),
            organizer=self.organizer,
            location=self.location,
            tickets_total=10,
            price_general=Decimal('100.00'),
            price_vip=Decimal('200.00'),
            status='activo'
        )

    def test_status_reprogramado_via_view(self):
        """Verifica que el estado cambia a 'reprogramado' al editar la fecha desde la vista."""
        self.client.login(username='organizador', password='organizador1234')
        url = reverse('event_edit', args=[self.event.id])
        new_date = (self.event.scheduled_at + timezone.timedelta(days=3)).date()
        new_time = self.event.scheduled_at.time().strftime('%H:%M')
        response = self.client.post(url, {
            'title': self.event.title,
            'description': self.event.description,
            'status': self.event.status,
            'date': new_date.strftime('%Y-%m-%d'),
            'time': new_time,
            'location': self.location.id,
            'price_general': self.event.price_general,
            'price_vip': self.event.price_vip,
            'tickets_total': self.event.tickets_total,
        })
        self.event.refresh_from_db()
        self.assertEqual(self.event.status, 'reprogramado')