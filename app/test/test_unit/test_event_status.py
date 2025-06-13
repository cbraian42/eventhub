from django.test import TestCase
from django.utils import timezone
import datetime
from decimal import Decimal

from app.models import Event, User, Location, Ticket

class EventDemandTest(TestCase):
    def setUp(self):
        # Crear usuario organizador
        self.organizer = User.objects.create_user(
            username="organizador",
            email="organizador@test.com",
            password="password123",
            is_organizer=True,
        )

        # Crear ubicación con capacidad
        self.location = Location.objects.create(
            name="Sala Principal",
            address="Calle Principal 123",
            city="Ciudad",
            capacity=100
        )

        # Crear evento
        self.event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            location=self.location,
            tickets_total=int("1"),
            price_general=Decimal('100.00'),
            price_vip=Decimal('200.00'),
            status='activo'
        )

    def test_status_reprogramado(self):
        """Test que verifica que el estado cambio si se reprograma el evento"""

        new_scheduled_at = timezone.now() + datetime.timedelta(days=3)
        self.event.update(
            title="Evento Reprogramado",
            description="Descripción del evento reprogramado",
            scheduled_at=new_scheduled_at,
            organizer=self.organizer,
            status=None  # Cambia el estado a None para reprogramar
        )

        # Verificar que el evento se ha reprogramado correctamente
        self.event.refresh_from_db()  # Actualizar el evento desde la base de datos
        self.assertEqual(self.event.status, "reprogramado")

    def test_status_agotado(self):
        """Test que verifica que el estado cambio si se vendieron todas las entradas"""
        # Vender todas las entradas
        Ticket.objects.create(
            event=self.event,
            user=self.organizer,
            type='general',
            quantity=self.event.tickets_total,
        )

        # Verificar que el estado del evento es agotado
        self.event.refresh_from_db()  # Actualizar el evento desde la base de datos
        self.assertEqual(self.event.status, "agotado")

    def test_status_activo(self):
        """Test que verifica que el estado por defecto es activo"""
        # Verificar que el estado del evento es activo por defecto
        self.assertEqual(self.event.status, "activo")