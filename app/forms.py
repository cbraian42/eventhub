from django import forms
from .models import Ticket, Coupon
from .models import Event
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from datetime import datetime
from django.db.models import Sum

class TicketForm(forms.ModelForm):
    card_number = forms.CharField(
        max_length=16, 
        min_length=16, 
        label="Número de tarjeta", 
        validators=[RegexValidator(r'^\d{16}$', message="Debe contener exactamente 16 dígitos numéricos.")],
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    card_cvv = forms.CharField(
        max_length=4, 
        label="CVV", 
        validators=[RegexValidator(r'^\d{3,4}$', message="Debe tener 3 o 4 dígitos numéricos.")],
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    MONTH_CHOICES = [(f"{i:02}", f"{i:02}") for i in range(1, 13)]
    expiry_month = forms.ChoiceField(
        choices=MONTH_CHOICES, 
        label="Mes",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    current_year = datetime.now().year
    YEAR_CHOICES = [(str(y)[-2:], str(y)) for y in range(current_year, current_year + 21)]
    expiry_year = forms.ChoiceField(
        choices=YEAR_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    quantity = forms.IntegerField(
        min_value=1,
        max_value=4,
        label="Cantidad de entradas",
        error_messages={
            'min_value': 'La cantidad mínima es 1 entrada',
            'max_value': 'No pueden comprarse más de 4 entradas',
            'invalid': 'Por favor ingrese un número válido'
        },
        widget=forms.NumberInput(attrs={'id': 'id_quantity', 'class': 'form-control'})
    )

    TYPE_CHOICES = [
        ('', 'Seleccione un tipo de entrada'),
        ('general', 'General'),
        ('vip', 'VIP'),
    ]

    type = forms.ChoiceField(
        choices=TYPE_CHOICES, 
        required=True, 
        label="Tipo de entrada", 
        widget=forms.Select(attrs={
            'id': 'id_type',
            'class': 'form-control'
        })
    )

    def clean_type(self):
        value = self.cleaned_data['type']
        if value == '':
            raise forms.ValidationError('Debe seleccionar un tipo de entrada.')
        return value

    class Meta:
        model = Ticket
        fields = ['event', 'quantity', 'type', 'card_type']
        labels = {
            'event': 'Evento',
            'type': 'Tipo de entrada',
            'card_type': 'Tipo de tarjeta',
        }
        widgets = {
            'event': forms.Select(attrs={'class': 'form-control'}),
            'card_type': forms.Select(attrs={'class': 'form-control'})
        }

    def clean(self):
        cleaned_data = super().clean()
        month = cleaned_data.get('expiry_month')
        year = cleaned_data.get('expiry_year')

        if month and year:
            now = datetime.now()
            exp_year = int('20' + year)
            exp_month = int(month)
            exp_date = datetime(exp_year, exp_month, 1)

            if exp_date.replace(day=28) < now.replace(day=1):
                self.add_error('expiry_month', 'La tarjeta ya está vencida.')

        quantity = cleaned_data.get('quantity')
        event = getattr(self, 'event_instance', None) or cleaned_data.get('event')
        user = getattr(self, 'user', None)

        if event and user and quantity:
            # Suma de entradas ya compradas por el usuario para este evento
            total_user_tickets = (
                Ticket.objects.filter(event=event, user=user).aggregate(Sum('quantity'))['quantity__sum'] or 0
            )
            
            if self.instance and self.instance.pk:
                total_user_tickets -= self.instance.quantity

            if total_user_tickets + quantity > 4:
                self.add_error('quantity', 'No pueden comprarse más de 4 entradas')

            # Validación de disponibilidad
            if quantity > event.tickets_available:
                self.add_error('quantity', f'Solo hay {event.tickets_available} tickets disponibles para este evento.')

        return cleaned_data

    def __init__(self, *args, user=None, fixed_event=False, event_instance=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user  

        if self.instance and self.instance.pk:
            masked = '************' + self.instance.last4_card_number
            self.fields['card_number'].initial = masked
            self.fields['card_number'].disabled = True
            self.fields['card_number'].validators.clear()

            self.fields['event'].disabled = True
            self.fields['card_type'].disabled = True

            self.fields.pop('card_cvv', None)
            self.fields.pop('expiry_month', None)
            self.fields.pop('expiry_year', None)

        if fixed_event and event_instance:
            self.fields.pop('event')
            self.event_instance = event_instance
        else:
            self.event_instance = None


class TicketFilterForm(forms.Form):
    event = forms.ModelChoiceField(queryset=Event.objects.none(), required=False, label="Evento")
    type = forms.ChoiceField(choices=[('', 'Todos'), ('general', 'General'), ('vip', 'VIP')], required=False, label="Tipo de entrada")
    date_from = forms.DateField(required=False, label="Desde", widget=forms.DateInput(attrs={'type': 'date'}))
    date_to = forms.DateField(required=False, label="Hasta", widget=forms.DateInput(attrs={'type': 'date'}))

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['event'].queryset = Event.objects.filter(organizer=user)


class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = ['coupon_code', 'discount_type', 'amount', 'active']
        widgets = {
            'coupon_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese el código del cupón'
            }),
            'discount_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),
            'active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'coupon_code': 'Código del Cupón',
            'discount_type': 'Tipo de Descuento',
            'amount': 'Valor del Descuento',
            'active': 'Activo'
        }

    def clean_coupon_code(self):
        coupon_code = self.cleaned_data.get('coupon_code')
        if not coupon_code:
            raise forms.ValidationError("El código del cupón es requerido.")
        return coupon_code

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise forms.ValidationError("El monto debe ser mayor a cero.")
        return amount
