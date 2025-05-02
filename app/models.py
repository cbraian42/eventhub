from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from decimal import Decimal
import uuid


class User(AbstractUser):
    is_organizer = models.BooleanField(default=False)

    @classmethod
    def validate_new_user(cls, email, username, password, password_confirm):
        errors = {}

        if email is None:
            errors["email"] = "El email es requerido"
        elif User.objects.filter(email=email).exists():
            errors["email"] = "Ya existe un usuario con este email"

        if username is None:
            errors["username"] = "El username es requerido"
        elif User.objects.filter(username=username).exists():
            errors["username"] = "Ya existe un usuario con este nombre de usuario"

        if password is None or password_confirm is None:
            errors["password"] = "Las contraseñas son requeridas"
        elif password != password_confirm:
            errors["password"] = "Las contraseñas no coinciden"

        return errors


class Location(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=300)
    city = models.CharField(max_length=100)
    capacity = models.PositiveIntegerField()
    contact = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} - {self.city}"

    @classmethod
    def validate(cls, name, address, city, capacity, contact):
        errors = {}

        if not name:
            errors["name"] = "El nombre es requerido."
        
        if not address:
            errors["address"] = "La dirección es requerida."
        
        if not city:
            errors["city"] = "La ciudad es requerida."
        
        if capacity is None:
            errors["capacity"] = "La capacidad es requerida."
        elif capacity <= 0:
            errors["capacity"] = "La capacidad debe ser un número positivo."
        
        if not contact:
            errors["contact"] = "El contacto es requerido."

        return errors

    @classmethod
    def new(cls, name, address, city, capacity, contact):
        errors = cls.validate(name, address, city, capacity, contact)
        if errors:
            return False, errors

        Location.objects.create(
            name=name,
            address=address,
            city=city,
            capacity=capacity,
            contact=contact,
        )

        return True, None

    def update(self, name=None, address=None, city=None, capacity=None, contact=None):
        self.name = name or self.name
        self.address = address or self.address
        self.city = city or self.city
        self.capacity = capacity if capacity is not None else self.capacity
        self.contact = contact or self.contact

        self.save()

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
    @classmethod
    def validate(cls, name, description):
        errors ={}

        if not name:
            errors["name"] = "El nombre es requerido."

        if not description:
            errors["description"] = "La descripción es requerida."
        
        return errors
    
    @classmethod
    def new(cls, name, description):
        errors = cls.validate(name, description)
        if errors:
            return False, errors

        Category.objects.create(
            name=name,
            description=description,
        )

        return True, None
    
    def update(self, name=None, description=None, is_active=None):
        self.name = name or self.name
        self.description = description or self.description

        if is_active is not None:
            self.is_active = is_active

        self.save()

class Ticket(models.Model):
    TYPE_CHOICES = [
        ('general', 'General'),
        ('vip', 'VIP'),
    ]

    buy_date = models.DateField(default=timezone.now)
    ticket_code = models.CharField(max_length=10, unique=True, editable=False)
    quantity = models.PositiveIntegerField()
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)

    def save(self, *args, **kwargs):
        if not self.ticket_code:
            self.ticket_code = str(uuid.uuid4())[:10].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ticket_code} - {self.type}"
    
   

    @classmethod
    def new(cls, buy_date, quantity, type):
       
        Ticket.objects.create(
            buy_date=buy_date,
            quantity=quantity,
            type=type,
        )

        return True, None

    def update(self, buy_date=None, quantity=None, type=None):
        self.buy_date = buy_date or self.buy_date
        self.type = type or self.type
        self.quantity = quantity if quantity is not None else self.quantity

        self.save()

class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    scheduled_at = models.DateTimeField()
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organized_events")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, related_name="events", null=True, blank=True)
    categories = models.ManyToManyField(Category, through='EventCategory')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))


    def __str__(self):
        return self.title

    @classmethod
    def validate(cls, title, description, scheduled_at, price):
        errors = {}

        if title == "":
            errors["title"] = "Por favor ingrese un titulo"

        if description == "":
            errors["description"] = "Por favor ingrese una descripcion"

        if price is not None and price < 0:
            errors["price"] = "El precio no puede ser negativo"

        return errors

    @classmethod
    def new(cls, title, description, scheduled_at, organizer, location=None, price=0.00):
        errors = Event.validate(title, description, scheduled_at, price)

        if len(errors.keys()) > 0:
            return False, errors

        event = Event.objects.create(
            title=title,
            description=description,
            scheduled_at=scheduled_at,
            organizer=organizer,
            location=location,
            price=price,
        )

        return event, None

    def update(self, title, description, scheduled_at, organizer, location=None, price=0.00):
        self.title = title or self.title
        self.description = description or self.description
        self.scheduled_at = scheduled_at or self.scheduled_at
        self.organizer = organizer or self.organizer
        self.location = location if location is not None else self.location
        self.price = price if price is not None else self.price

        self.save()

class EventCategory(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('event', 'category')

    def __str__(self):
        return f"{self.event.title} - {self.category.name}"

class Notification(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    priority = models.CharField(max_length=50, choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')])
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="notifications", null=True, blank=True)

    def __str__(self):
        return f"{self.title} - {self.created_at}"
    
    @classmethod
    def validate(cls, title, message, event_id, recipient_type, specific_user_id):
        errors = {}

        if not title:
            errors["title"] = "El título es requerido."
        
        if not message:
            errors["message"] = "El mensaje es requerido."
        
        if recipient_type == "event" and not event_id:
            errors["event"] = "El evento es requerido."
        
        if recipient_type == "specific" and not specific_user_id:
            errors["user"] = "El usuario específico es requerido."

        return errors
    
    @classmethod
    def new(cls, title, message, event, priority):
        notification = Notification.objects.create(
            title=title,
            message=message,
            event=event,
            priority=priority,
        )
        return notification
    
class NotificationXUser(models.Model):
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name="notification_user")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_notification")
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.notification} - {self.user}"
    
    @classmethod
    def new(cls, notification, user):
        notification_user = NotificationXUser.objects.create(
            notification=notification,
            user=user,
        )
        return notification_user
    