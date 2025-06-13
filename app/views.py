import datetime
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.db.models import Count
from .models import Event, User, Location, Category, Notification, NotificationXUser, Comments, Ticket, Coupon
from .forms import TicketForm, TicketFilterForm, CouponForm
from django.http import Http404
from django.conf import settings
import pytz
from django.http import JsonResponse
from decimal import Decimal
from django.utils import timezone

def register(request):
    if request.method == "POST":
        email = request.POST.get("email")
        username = request.POST.get("username")
        is_organizer = request.POST.get("is-organizer") is not None
        password = request.POST.get("password")
        password_confirm = request.POST.get("password-confirm")

        errors = User.validate_new_user(email, username, password, password_confirm)

        if len(errors) > 0:
            return render(
                request,
                "accounts/register.html",
                {
                    "errors": errors,
                    "data": request.POST,
                },
            )
        else:
            user = User.objects.create_user(
                email=email, username=username, password=password, is_organizer=is_organizer
            )
            login(request, user)
            return redirect("events")

    return render(request, "accounts/register.html", {})


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is None:
            return render(
                request, "accounts/login.html", {"error": "Usuario o contraseña incorrectos"}
            )

        login(request, user)
        return redirect("events")

    return render(request, "accounts/login.html")


def home(request):
    return render(request, "home.html")


@login_required
def events(request):
    """Vista para listar eventos"""
    # Obtener el parámetro show_past de la URL
    show_past = request.GET.get("show_past", "false").lower() == "true"

    # Obtener la hora actual
    current_time = timezone.now()

    # Obtener eventos según el filtro
    if show_past:
        events = Event.objects.all().order_by("-scheduled_at")
    else:
        events = Event.objects.filter(scheduled_at__gte=current_time).order_by("scheduled_at")

    # Verificar si el usuario es organizador
    user_is_organizer = request.user.is_organizer

    return render(
        request,
        "app/events.html",
        {
            "events": events,
            "show_past": show_past,
            "user_is_organizer": user_is_organizer,
        },
    )


@login_required
def event_detail(request, id):
    event = get_object_or_404(Event, id=id)
    comments = Comments.objects.filter(event=event).order_by('-created_at')
    user_is_organizer = request.user.is_authenticated and request.user.is_organizer

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        errors = {}

        if not title:
            errors['title'] = "El título no puede estar vacío."
        if not description:
            errors['description'] = "La descripción no puede estar vacía."

        if not errors:
            Comments.objects.create(
                title=title,
                description=description,
                user=request.user,
                event=event
            )
            return redirect('event_detail', id=event.id)

        # Si hay errores, los devolvemos al template
        return render(request, 'app/event_detail.html', {
            'event': event,
            'comments': comments,
            'errors': errors,
            'title': title,
            'description': description,
            'user_is_organizer': user_is_organizer,
            'demand_status': event.demand_status,
            'tickets_sold': event.tickets_sold,
            'tickets_available': event.tickets_available
        })

    context = {
        'event': event,
        'comments': comments,
        'user_is_organizer': user_is_organizer,
        'demand_status': event.demand_status,
        'tickets_sold': event.tickets_sold,
        'tickets_available': event.tickets_available
    }
    
    return render(request, 'app/event_detail.html', context)


@login_required
def event_delete(request, id):
    user = request.user
    if not user.is_organizer:
        return redirect("events")

    if request.method == "POST":
        event = get_object_or_404(Event, pk=id)
        event.delete()
        return redirect("events")

    return redirect("events")


@login_required
def event_form(request, id=None):
    user = request.user

    if not user.is_organizer:
        return redirect("events")

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        status = request.POST.get("status")
        date = request.POST.get("date")
        time = request.POST.get("time")
        location_id = request.POST.get("location")
        location = Location.objects.filter(id=location_id).first() if location_id else None
        category_ids = request.POST.getlist("categories")
        categories = Category.objects.filter(id__in=category_ids)
        price_general = request.POST.get("price_general")
        price_vip = request.POST.get("price_vip")
        tickets_total = request.POST.get("tickets_total")

        [year, month, day] = date.split("-")
        [hour, minutes] = time.split(":")
        # Guardar el datetime como aware en la zona horaria local y convertir a UTC
        naive_datetime = datetime.datetime(int(year), int(month), int(day), int(hour), int(minutes))
        local_tz = pytz.timezone(settings.TIME_ZONE)
        local_aware_datetime = local_tz.localize(naive_datetime)
        scheduled_at = local_aware_datetime.astimezone(pytz.UTC)

        if id is None:
            event, errors = Event.new(title, description, scheduled_at, request.user, location, status=status)
        else:
            event = get_object_or_404(Event, pk=id)
            if event.scheduled_at != scheduled_at:
                status = 'reprogramado'
            event.update(title, description, scheduled_at, request.user, status, location)

        if event:
            if price_general is not None:
                event.price_general = float(str(price_general).replace(',', '.'))
            if price_vip is not None:
                event.price_vip = float(str(price_vip).replace(',', '.'))
            
            event.categories.set(categories)
            event.tickets_total = int(tickets_total) if tickets_total is not None else 0

            event.save()
        return redirect('events')

    if id is not None:
        event = get_object_or_404(Event, pk=id)
        if event.price_general is not None:
            event.price_general = float(str(event.price_general).replace(',', '.'))
        if event.price_vip is not None:
            event.price_vip = float(str(event.price_vip).replace(',', '.'))
    else:
        event = Event()

    locations = Location.objects.all()
    categories = Category.objects.all()

    return render(
        request,
        "app/event_form.html",
        {"event": event, "user_is_organizer": request.user.is_organizer, "locations": locations, "categories": categories},
    )



@login_required
def list_locations(request):
    locations = Location.objects.all() # Las más nuevas primero
    return render(request, 'locations/list_locations.html', {'locations': locations})

@login_required
def create_location(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address')
        city = request.POST.get('city')
        capacity = request.POST.get('capacity')
        contact = request.POST.get('contact')

        # Validar datos
        errors = Location.validate(name, address, city, int(capacity) if capacity else None, contact)

        if errors:
            # Si hay errores, renderizamos el formulario otra vez, mostrando errores
            return render(request, 'locations/create_location.html', {
                'errors': errors,
                'form_data': request.POST,
            })

        # Si no hay errores, creamos la Location
        Location.new(name, address, city, int(capacity), contact)
        return redirect('locations_list')  # Redirigimos a una lista o donde quieras

    return render(request, 'locations/create_location.html')

def update_location(request, location_id):
    location = get_object_or_404(Location, id=location_id)

    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address')
        city = request.POST.get('city')
        capacity = request.POST.get('capacity')
        contact = request.POST.get('contact')

        errors = Location.validate(name, address, city, int(capacity) if capacity else None, contact)

        if errors:
            return render(request, 'locations/update_location.html', {
                'location': location,
                'errors': errors,
                'form_data': request.POST,
            })

        location.update(name=name, address=address, city=city, capacity=int(capacity), contact=contact)
        return redirect('locations_list')

    return render(request, 'locations/update_location.html', {'location': location})

def delete_location(request, location_id):
    location = get_object_or_404(Location, id=location_id)
    location.delete()
    return redirect('locations_list')

@login_required
def list_categories(request):
    categories = Category.objects.annotate(event_qty=Count('eventcategory'))
    return render(request, 'categories/list_categories.html', {'categories': categories})

@login_required
def manage_category(request, category_id=None):
    category = None
    if category_id:
        category = get_object_or_404(Category, id=category_id)

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        is_active = request.POST.get('is_active') == 'on' if category else True

        errors = Category.validate(name, description)

        if errors:
            return render(request, 'categories/create_category.html', {
                'category': category,
                'errors': errors,
                'form_data': request.POST,
            })

        if category:
            category.update(name=name, description=description, is_active=is_active)
        else:
            Category.new(name, description)

        return redirect('categories_list')

    return render(request, 'categories/create_category.html', {
        'category': category
    })
    
@login_required
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    category.delete()
    return redirect('categories_list')

@login_required
def create_notification(request, notification_id=None):
    user = request.user
    if not user.is_organizer:
        return redirect("list_notifications")
    
    events = Event.objects.all()
    users = User.objects.all()

    notification = None
    if notification_id:
        notification = get_object_or_404(Notification, id=notification_id)

    if request.method == 'POST':
        title = request.POST.get('title')
        message = request.POST.get('message')
        event_id = request.POST.get('event')
        priority = request.POST.get('priority')
        recipient_type = request.POST.get('recipients')
        specific_user_id = request.POST.get('userSelect') if recipient_type == 'specific' else None

        errors = Notification.validate(title, message, event_id, recipient_type, specific_user_id)
        if errors:
            return render(request, 'notifications/create_notification.html', {
                'events': events,
                'users': users,
                'errors': errors,
                'form_data': request.POST,
                'notification': notification,
            })

        event_selected = Event.objects.get(id=event_id)
        if notification:

            notification.title = title
            notification.message = message
            notification.event = event_selected
            notification.priority = priority
            notification.save()


            NotificationXUser.objects.filter(notification=notification).delete()
        else:

            notification = Notification.new(title, message, event_selected, priority)


        if recipient_type == 'all':
            for user in users:
                NotificationXUser.objects.create(notification=notification, user=user)
        elif recipient_type == 'specific' and specific_user_id:
            specific_user = User.objects.get(id=specific_user_id)
            NotificationXUser.objects.create(notification=notification, user=specific_user)


        return redirect('list_notifications')


    return render(request, 'notifications/create_notification.html', {
        'events': events,
        'users': users,
        'notification': notification,
    })

@login_required
def list_notifications(request):
    search = request.GET.get('search', '')
    event_filter = request.GET.get('event_filter', '')
    priority_filter = request.GET.get('priority_filter', '')

    if request.user.is_organizer:
        notifications = Notification.objects.all()
        if search:
            notifications = notifications.filter(title__icontains=search)
        if event_filter:
            notifications = notifications.filter(event_id=event_filter)
        if priority_filter:
            notifications = notifications.filter(priority=priority_filter)

        events = Event.objects.all()
        users = User.objects.all()

        return render(request, 'notifications/notifications_admin.html', {
            'notifications': notifications,
            'events': events,
            'users': users,
        })
    else:  # user normal
        notifications = NotificationXUser.objects.filter(user=request.user).select_related('notification')
        unread_count = notifications.filter(is_read=False).count()
        return render(request, 'notifications/notifications_user.html', {
            'notifications': notifications,
            'unread_count': unread_count,
        })

@login_required
def delete_notification(request, notification_id):
    user = request.user
    if not user.is_organizer:
        return redirect("list_notifications")
    
    notification = get_object_or_404(Notification, id=notification_id)
    notification.delete()
    return redirect('list_notifications')

@login_required
def read_notification(request, notification_user_id):
    notification_user = get_object_or_404(NotificationXUser, id=notification_user_id, user=request.user)
    notification_user.is_read = True
    notification_user.save()
    return redirect('list_notifications')

@login_required
def read_all_notifications(request):
    NotificationXUser.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect('list_notifications')

def edit_comment(request, comment_id):
    comment = get_object_or_404(Comments, pk=comment_id, user=request.user)

    if request.method == "POST":
        comment.title = request.POST.get('title', '')
        comment.description = request.POST.get('description', '')
        comment.save()
        return redirect('event_detail', id=comment.event.id)

    return render(request, 'comments/edit_comment.html', {'comment': comment})

def delete_comment(request, comment_id):
    try:
        comment = Comments.objects.get(id=comment_id)
    except Comments.DoesNotExist:
        messages.error(request, "Comentario no encontrado.")
        return redirect('event_list')
    
    if request.user != comment.user and not request.user.is_staff:
        messages.error(request, "No tienes permiso para eliminar este comentario.")
        return redirect('event_detail', id=comment.event.id)

    if request.method == 'POST':
        comment.delete()
        messages.success(request, "Comentario eliminado exitosamente.")
        return redirect('event_detail', id=comment.event.id)

    return render(request, 'comments/delete_comment.html', {'comment': comment})


def detail_comment(request, comment_id):
    comment = get_object_or_404(Comments, pk=comment_id)
    return render(request, 'comments/detail_comment.html', {'comment': comment})

@login_required
def tickets_list(request):
    ticket = Ticket.objects.filter(user=request.user)
    return render(request, "tickets/tickets_list.html", {"tickets": ticket})

@login_required
def organizer_tickets_list(request):
    events = Event.objects.all()
    organizer_events = Event.objects.filter(organizer=request.user)
    tickets = Ticket.objects.filter(event__in=organizer_events)

    form = TicketFilterForm(request.GET or None, user=request.user)

    if form.is_valid():
        if form.cleaned_data['event']:
            tickets = tickets.filter(event=form.cleaned_data['event'])
        if form.cleaned_data['type']:
            tickets = tickets.filter(type=form.cleaned_data['type'])
        if form.cleaned_data['date_from']:
            tickets = tickets.filter(buy_date__date__gte=form.cleaned_data['date_from'])
        if form.cleaned_data['date_to']:
            tickets = tickets.filter(buy_date__date__lte=form.cleaned_data['date_to'])

    return render(request, "tickets/organizer_tickets_list.html", {
        "tickets": tickets,
        "form": form,
        'events': events
    })

@login_required
def buy_ticket(request):
    if request.method == 'POST':
        form = TicketForm(request.POST, user=request.user)
        if form.is_valid():
            event = form.cleaned_data['event']
            type_ = form.cleaned_data['type']
            quantity = form.cleaned_data['quantity']
            card_number = form.cleaned_data['card_number']
            card_cvv = form.cleaned_data['card_cvv']

            if len(card_number) != 16:
                form.add_error('card_number', 'El número debe tener 16 dígitos.')
                return render(request, 'tickets/buy_ticket.html', {
                    'form': form,
                    'price_general': event.price_general,
                    'price_vip': event.price_vip
                })

            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.last4_card_number = card_number[-4:]
            ticket.save() 
            
            return redirect('tickets_list')
    else:
        form = TicketForm(user=request.user)

    events = Event.objects.all()
    event_prices = {
        event.id: {
            'general': float(event.price_general),
            'vip': float(event.price_vip)
        } for event in events
    }

    return render(request, 'tickets/buy_ticket.html', {
        'form': form,
        'event_prices': event_prices
    })

@login_required
def delete_ticket(request, ticket_code):
    ticket = get_object_or_404(Ticket, ticket_code=ticket_code)

    # Permitir eliminar solo si el usuario es dueño del ticket o organizador del evento
    if ticket.user != request.user and ticket.event.organizer != request.user:
        raise Http404("No tienes permiso para eliminar este ticket.")

    ticket.delete()
    if request.user.is_organizer:
        return redirect('organizer_tickets_list')
    return redirect('tickets_list')


@login_required
def update_ticket(request, ticket_code):
    ticket = get_object_or_404(Ticket, ticket_code=ticket_code, user=request.user)
    
    # Prepara los precios de los eventos para el contexto
    event_prices = {}
    if ticket.event:
        event_prices[str(ticket.event.id)] = {
            'general': float(ticket.event.price_general),
            'vip': float(ticket.event.price_vip)
        }

    if request.method == 'POST':
        form = TicketForm(request.POST, instance=ticket, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('tickets_list')
        return render(request, 'tickets/update_ticket.html', {
            'form': form,
            'event_prices': event_prices
        })
    else:
        form = TicketForm(instance=ticket, user=request.user)
        return render(request, 'tickets/update_ticket.html', {
            'form': form,
            'event_prices': event_prices,
            'ticket': ticket  # Opcional: por si necesitas otros datos del ticket
        })

@login_required
def buy_ticket_from_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    applied_coupon = None
    discount_amount = Decimal('0.00')
    coupon_message = ""
    coupon_error = ""

    if request.method == 'POST':
        if 'apply_coupon' in request.POST:
            form = TicketForm(request.POST, fixed_event=True, event_instance=event)
            coupon_code = request.POST.get('coupon_code', '').strip()
            if coupon_code:
                try:
                    applied_coupon = Coupon.objects.get(coupon_code=coupon_code, active=True)
                    coupon_message = f"Cupón aplicado: {applied_coupon.get_discount_type_display()} de {applied_coupon.amount}"
                    if applied_coupon.discount_type == 'percent':
                        coupon_message += "%"
                    else:
                        coupon_message += "$"
                except Coupon.DoesNotExist:
                    coupon_error = "Cupón no válido o inactivo"
        else:
            form = TicketForm(request.POST, fixed_event=True, event_instance=event)
            if form.is_valid():
                # VERIFICAR DISPONIBILIDAD ANTES DE COMPRAR
                quantity = form.cleaned_data['quantity']
                if event.tickets_available < quantity:
                    messages.error(request, "No hay suficientes tickets disponibles")
                    return redirect('buy_ticket_from_event', event_id=event.id)
                
                ticket = form.save(commit=False)
                ticket.user = request.user
                ticket.event = event
                
                coupon_code = request.POST.get('coupon_code', '').strip()
                if coupon_code:
                    try:
                        applied_coupon = Coupon.objects.get(coupon_code=coupon_code, active=True)
                        ticket.coupon = applied_coupon
                    except Coupon.DoesNotExist:
                        pass
                
                ticket.save()
                return redirect('tickets_list')
    else:
        form = TicketForm(fixed_event=True, event_instance=event)

    # Calcular precios para el resumen
    price_per_ticket = Decimal(str(event.price_general if form.data.get('type', 'general') == 'general' else event.price_vip))
    quantity = int(form.data.get('quantity', 1))
    subtotal = price_per_ticket * quantity
    tax = subtotal * Decimal('0.10')
    total = subtotal + tax
    
    if applied_coupon:
        discount_amount = applied_coupon.amount if applied_coupon.discount_type == 'fixed' else (total * (applied_coupon.amount / Decimal('100.00')))
        total = max(total - discount_amount, Decimal('0.00'))

    return render(request, 'tickets/buy_ticket.html', {
        'price_general': float(event.price_general),
        'price_vip': float(event.price_vip),
        'form': form,
        'event': event,
        'applied_coupon': applied_coupon,
        'coupon_message': coupon_message,
        'coupon_error': coupon_error,
        'price_per_ticket': price_per_ticket,
        'subtotal': subtotal,
        'tax': tax,
        'total': total,
        'discount_amount': discount_amount,
    })


@login_required
def toggle_favorite(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    user = request.user

    if user.es_evento_favorito(event):
        user.desmarcar_evento_favorito(event)
        messages.success(request, f'"{event.title}" removido de favoritos')
    else:
        user.marcar_evento_favorito(event)
        messages.success(request, f'"{event.title}" agregado a favoritos')

    return redirect('events')


@login_required
def my_favorites(request):
    """Vista para mostrar eventos favoritos del usuario"""
    return render(request, 'favoritos/my_favorites.html')

def coupon_list_create(request):
    coupons = Coupon.objects.all().order_by('coupon_code')

    if request.method == 'POST':
        form = CouponForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('coupon_list_create')
    else:
        form = CouponForm()

    context = {
        'coupons': coupons,
        'form': form,
    }
    return render(request, 'coupons/coupon_list_create.html', context)

def coupon_delete(request, pk):
    coupon = get_object_or_404(Coupon, pk=pk)
    if request.method == 'POST':
        coupon.delete()
        return redirect('coupon_list_create')
    return render(request, 'coupons/coupon_confirm_delete.html', {'coupon': coupon})

@login_required
def toggle_coupon_active(request, pk):
    coupon = get_object_or_404(Coupon, pk=pk)
    coupon.active = not coupon.active
    coupon.save()
    return redirect('coupon_list_create')

@login_required
def validate_coupon(request):
    coupon_code = request.GET.get('code', '').strip()
    response_data = {'valid': False, 'message': ''}
    
    if coupon_code:
        try:
            coupon = Coupon.objects.get(coupon_code=coupon_code, active=True)
            response_data['valid'] = True
            response_data['coupon'] = {
                'discount_type': coupon.discount_type,
                'amount': float(coupon.amount)
            }
        except Coupon.DoesNotExist:
            response_data['message'] = 'Cupón no válido o inactivo'
    else:
        response_data['message'] = 'Por favor ingrese un código de cupón'
    
    return JsonResponse(response_data)