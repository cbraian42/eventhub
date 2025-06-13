import datetime
from django.utils import timezone
from decimal import Decimal
from playwright.sync_api import expect

from app.models import Event, User, Location
from app.test.test_e2e.base import BaseE2ETest

class EventStatusE2ETest(BaseE2ETest):
    def setUp(self):
        super().setUp()

        # Crear usuario organizador
        self.organizer = User.objects.create_user(
            username="organizador",
            email="organizador@example.com",
            password="password123",
            is_organizer=True,
        )

        # Crear usuario regular
        self.regular_user = User.objects.create_user(
            username="usuario",
            email="usuario@gmail.com",
            password="usuario1234",
            is_organizer=False,
        )

        # Crear ubicación
        self.location = Location.objects.create(
            name="Castillo prueba",
            address="Calle Principal",
            city="La Plata",
            capacity=100
        )

        # Crear evento con estado "activo"
        self.event = Event.objects.create(
            title="Evento E2E",
            description="Descripción E2E",
            scheduled_at=timezone.now() + datetime.timedelta(days=2),
            organizer=self.organizer,
            location=self.location,
            tickets_total=10,
            price_general=Decimal('100.00'),
            price_vip=Decimal('200.00'),
            status='activo'
        )

    def test_user_status_eventDetail(self):
        """Confirma que el usuario final ve el estado correcto en la UI."""
        # Login como usuario regular
        self.login_user("usuario", "usuario1234")

        # Ir a la página de detalle del evento
        self.page.goto(f"{self.live_server_url}/events/{self.event.id}/")

        # Verificar que el estado se muestra correctamente en la UI
        status_element = self.page.locator("#event-status")
        expect(status_element).to_be_visible()
        expect(status_element).to_have_text(self.event.status)