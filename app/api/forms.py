from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from .models import (
    Organization, City, User, PurchaserProfile,
    Product, AlcoholProduct, Supplier, Price, 
    SupplierToken, PriceRequest
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

class PriceRequestForm(forms.ModelForm):
    """
    Форма для создания/редактирования запроса цены.
    Предназначена в первую очередь для внутреннего использования.
    """
    class Meta:
        model = PriceRequest
        # Исключаем поля, которые устанавливаются автоматически или требуют специальной логики
        exclude = ('purchaser', 'created_at', 'updated_at') 
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Добавьте комментарий к запросу, если необходимо...'}),
            'status': forms.Select(), # Если нужно разрешить редактирование статуса вручную
        }

    def __init__(self, *args, **kwargs):
        # Передаем пользователя для фильтрации queryset'ов
        self.user = kwargs.pop('user', None) 
        super().__init__(*args, **kwargs)
        
        if self.user:
            # Фильтруем поставщиков и товары в зависимости от прав пользователя
            if self.user.role == 'admin':
                # Админ видит всех
                pass 
            elif hasattr(self.user, 'purchaser_profile'):
                profile = self.user.purchaser_profile
                orgs = profile.organizations.all()
                
                # Фильтруем поставщиков и товары по организациям пользователя
                self.fields['supplier'].queryset = Supplier.objects.filter(organization__in=orgs)
                self.fields['product'].queryset = Product.objects.filter(organization__in=orgs)
                self.fields['alcohol'].queryset = AlcoholProduct.objects.filter(organization__in=orgs)
            else:
                # Если профиля нет, оставляем пустые queryset'ы или обрабатываем иначе
                self.fields['supplier'].queryset = Supplier.objects.none()
                self.fields['product'].queryset = Product.objects.none()
                self.fields['alcohol'].queryset = AlcoholProduct.objects.none()
                
        # Если форма редактируется (instance существует), можно ограничить редактируемые поля
        if self.instance and self.instance.pk:
            # Например, запретить изменение товара/алкоголя после создания
            self.fields['product'].disabled = True
            self.fields['alcohol'].disabled = True
            self.fields['supplier'].disabled = True
            
            # Ограничиваем изменение статуса (например, нельзя вернуться из 'responded' в 'pending')
            # Это логика может быть сложнее и лучше реализована в модели или представлении
            # current_status = self.instance.status
            # if current_status in ['responded', 'cancelled']:
            #     self.fields['status'].disabled = True

    def clean(self):
        """
        Кастомная валидация формы.
        """
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        alcohol = cleaned_data.get('alcohol')
        supplier = cleaned_data.get('supplier')

        # Проверка, что указан только один товар
        if not product and not alcohol:
            raise forms.ValidationError("Необходимо выбрать либо продукт, либо алкоголь.")
        if product and alcohol:
            raise forms.ValidationError("Можно выбрать только один товар (продукт или алкоголь).")
            
        # Проверка соответствия поставщика и товара по организации (если нужно)
        # item = product or alcohol
        # if item and supplier and item.organization != supplier.organization:
        #     raise forms.ValidationError("Поставщик и товар должны принадлежать одной организации.")
            
        return cleaned_data

# Форма для изменения статуса (например, для поставщика)
class PriceRequestStatusForm(forms.ModelForm):
    """
    Форма только для изменения статуса запроса.
    """
    class Meta:
        model = PriceRequest
        fields = ('status',)