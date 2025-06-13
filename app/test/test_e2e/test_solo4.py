from app.test.test_e2e.base import BaseE2ETest 
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from app.models import Event, Ticket, User


class EditarTicketE2ETest(BaseE2ETest):
    
    def setUp(self):
        super().setUp()
        
        # Crear usuario organizador
        self.user = self.create_test_user(is_organizer=True)
        
        # Crear evento
        self.event = Event.objects.create(
            title="Evento E2E",
            description="Desc",
            scheduled_at=timezone.now() + timezone.timedelta(days=5),
            organizer=self.user,
            price_general=Decimal("50.00"),
            price_vip=Decimal("100.00")
        )
        
        # Ticket original con 2 entradas
        self.ticket = Ticket.objects.create(
            user=self.user, 
            event=self.event, 
            quantity=2, 
            type='general',
            card_type='debit'
        )
        
        # Otro ticket para sumar hasta 4 (total de 4 entradas ya compradas)
        Ticket.objects.create(
            user=self.user, 
            event=self.event, 
            quantity=2, 
            type='vip'
        )

    def test_no_puede_editar_ticket_si_supera_maximo(self):

        # Login usando el método del BaseE2ETest
        self.login_user("usuario_test", "password123")
        
        # Navegar a la página de edición del ticket
        self.page.goto(f"{self.live_server_url}/tickets/{self.ticket.ticket_code}/edit/")
        
        # Verificar que estamos en la página correcta
        # Esperar explícitamente que aparezca el contenido esperado
        self.page.wait_for_selector("h3", timeout=5000)
        assert self.page.locator("h3").filter(has_text="Editar Ticket").is_visible()

        
        # Cambiar la cantidad a 3 (que haría superar el límite de 4)
        self.page.fill("#id_quantity", "3")

        
        # Seleccionar tipo general si es necesario
        type_select = self.page.locator("#id_type")
        if type_select.count() > 0:
            type_select.select_option("general")
        
        # Enviar el formulario usando el botón específico
        submit_btn = self.page.locator("#submitBtn")
        submit_btn.click()
        
        # Verificar que aparece el mensaje de error en el alert
        error_alert = self.page.locator(".alert-danger")
        assert error_alert.is_visible()
        assert self.page.locator("text=No pueden comprarse más de 4 entradas").is_visible()
        
        # Verificar que seguimos en la página de edición (no se guardó)
        assert "/edit/" in self.page.url
        
        # Opcional: Verificar que la cantidad no cambió en la base de datos
        self.ticket.refresh_from_db()
        assert self.ticket.quantity == 2, "La cantidad del ticket no debería haber cambiado"
