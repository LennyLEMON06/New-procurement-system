from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from .models import (
    Organization, City, User, PurchaserProfile,
    Product, AlcoholProduct, Supplier, Price, SupplierToken
)
from django.utils.translation import gettext_lazy as _
import uuid
from django.utils.timezone import now
from datetime import timedelta

## User Forms ##

class UserRegistrationForm(UserCreationForm):
    phone = forms.CharField(max_length=20, required=False, label=_("Телефон"))
    role = forms.ChoiceField(choices=User.ROLES, label=_("Роль"))

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'role', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True

class UserUpdateForm(UserChangeForm):
    password = None  # Убираем поле смены пароля
    phone = forms.CharField(max_length=20, required=False, label=_("Телефон"))

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'role', 'is_active')

class PurchaserProfileForm(forms.ModelForm):
    organizations = forms.ModelMultipleChoiceField(
        queryset=Organization.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label=_("Доступные организации")
    )
    cities = forms.ModelMultipleChoiceField(
        queryset=City.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label=_("Доступные города")
    )

    class Meta:
        model = PurchaserProfile
        fields = ('organizations', 'cities')

## Organization Forms ##

class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ('name', 'description')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

## City Forms ##

class CityForm(forms.ModelForm):
    class Meta:
        model = City
        fields = ('name',)

## Product Forms ##

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ('name', 'quantity', 'unit', 'organization')
        widgets = {
            'organization': forms.Select(attrs={'class': 'select2'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user and not user.is_superuser:
            # Ограничиваем выбор организаций для не-админов
            if hasattr(user, 'purchaser_profile'):
                self.fields['organization'].queryset = user.purchaser_profile.organizations.all()

class AlcoholProductForm(forms.ModelForm):
    class Meta:
        model = AlcoholProduct
        exclude = ('name', 'organization', 'last_updated')
        widgets = {
            'strength': forms.NumberInput(attrs={'step': '0.01'}),
        }

## Supplier Forms ##

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ('name', 'contact_info', 'inn', 'city', 'organization')
        widgets = {
            'contact_info': forms.Textarea(attrs={'rows': 3}),
            'organization': forms.Select(attrs={'class': 'select2'}),
            'city': forms.Select(attrs={'class': 'select2'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user and not user.is_superuser:
            # Ограничиваем выбор организаций для не-админов
            if hasattr(user, 'purchaser_profile'):
                self.fields['organization'].queryset = user.purchaser_profile.organizations.all()

class SupplierTokenForm(forms.ModelForm):
    regenerate = forms.BooleanField(
        required=False,
        initial=False,
        label=_("Сгенерировать новый токен"),
        help_text=_("При включении будет создан новый токен, старый перестанет работать")
    )

    class Meta:
        model = SupplierToken
        fields = ('supplier', 'regenerate')

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.cleaned_data['regenerate']:
            instance.token = uuid.uuid4()
            instance.created_at = now()
        
        if commit:
            instance.save()
        
        return instance

## Price Forms ##

class PriceForm(forms.ModelForm):
    class Meta:
        model = Price
        fields = ('product', 'supplier', 'price', 'manufacturer')
        widgets = {
            'product': forms.Select(attrs={'class': 'select2'}),
            'supplier': forms.Select(attrs={'class': 'select2'}),
            'price': forms.NumberInput(attrs={'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user and not user.is_superuser:
            # Ограничиваем выбор продуктов и поставщиков для не-админов
            if hasattr(user, 'purchaser_profile'):
                orgs = user.purchaser_profile.organizations.all()
                self.fields['product'].queryset = Product.objects.filter(organization__in=orgs)
                self.fields['supplier'].queryset = Supplier.objects.filter(organization__in=orgs)

class PriceBulkForm(forms.Form):
    supplier = forms.ModelChoiceField(queryset=Supplier.objects.all(), label=_("Поставщик"))
    price_file = forms.FileField(label=_("Файл с ценами (CSV)"))

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user and not user.is_superuser:
            if hasattr(user, 'purchaser_profile'):
                orgs = user.purchaser_profile.organizations.all()
                self.fields['supplier'].queryset = Supplier.objects.filter(organization__in=orgs)