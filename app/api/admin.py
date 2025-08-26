from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Organization, City, User, PurchaserProfile, 
    Product, AlcoholProduct, Supplier, SupplierToken, 
    Price, PriceAlcohol, PriceRequest
)
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django import forms

# Кастомные формы для пользователя
class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User

    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(self.error_messages['duplicate_username'])

# Кастомный админ для пользователя
class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'phone')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions', 'role')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'role', 'phone')}
        ),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'role')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'role')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'phone')
    ordering = ('username',)

# Фильтр по организации
class OrganizationFilter(admin.SimpleListFilter):
    title = 'Организация'
    parameter_name = 'organization'

    def lookups(self, request, model_admin):
        organizations = Organization.objects.all()
        return [(org.id, org.name) for org in organizations]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(organization_id=self.value())
        return queryset

# Админка для продукта
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'quantity', 'unit', 'organization', 'last_updated')
    list_filter = (OrganizationFilter, 'unit')
    search_fields = ('name', 'organization__name')
    list_per_page = 20

# Админка для алкогольного продукта
class AlcoholProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'excise_stamp_required', 'organization')
    list_filter = ('excise_stamp_required', OrganizationFilter)
    search_fields = ('name',)

# Админка для поставщика
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'inn', 'type','city', 'organization')
    list_filter = (OrganizationFilter, 'city')
    search_fields = ('name', 'inn', 'contact_info')
    list_per_page = 20

# Админка для токена поставщика
class SupplierTokenAdmin(admin.ModelAdmin):
    list_display = ('supplier', 'token', 'created_at', 'is_expired')
    list_filter = (OrganizationFilter,)
    search_fields = ('supplier__name', 'token')
    readonly_fields = ('created_at', 'is_expired')
    
    def is_expired(self, obj):
        return obj.is_expired()
    is_expired.boolean = True
    is_expired.short_description = 'Истек'

# Админка для цен на продукты
class PriceAdmin(admin.ModelAdmin):
    list_display = ('product', 'supplier_name', 'price', 'manufacturer', 'date_added', 'date_updated')
    list_filter = (OrganizationFilter, 'date_added')
    search_fields = ('product__name', 'supplier__name', 'manufacturer')
    list_per_page = 20
    raw_id_fields = ('product', 'supplier')
    
    def supplier_name(self, obj):
        return obj.supplier.name
    supplier_name.short_description = 'Поставщик'

# Админка для цен на алкоголь
class PriceAlcoholAdmin(admin.ModelAdmin):
    list_display = ('alcohol', 'supplier_name', 'price', 'manufacturer', 'date_added', 'date_updated')
    list_filter = (OrganizationFilter, 'date_added')
    search_fields = ('alcohol__name', 'supplier__name', 'manufacturer')
    list_per_page = 20
    raw_id_fields = ('alcohol', 'supplier')
    
    def supplier_name(self, obj):
        return obj.supplier.name
    supplier_name.short_description = 'Поставщик'

# Админка для профиля закупщика
class PurchaserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'display_organizations', 'display_cities')
    filter_horizontal = ('organizations', 'cities')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    raw_id_fields = ('user',)
    
    def display_organizations(self, obj):
        return ", ".join([org.name for org in obj.organizations.all()])
    display_organizations.short_description = 'Организации'
    
    def display_cities(self, obj):
        return ", ".join([city.name for city in obj.cities.all()])
    display_cities.short_description = 'Города'

# Админка для запросов цен
class PriceRequestAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'get_item_name', 'purchaser_name', 'supplier_name', 
        'status', 'created_at', 'updated_at'
    )
    list_filter = (
        'status', 'created_at', 'updated_at', 
        OrganizationFilter, # Используем существующий фильтр по организации
    )
    search_fields = (
        'purchaser__username', 'purchaser__first_name', 'purchaser__last_name',
        'supplier__name', 'product__name', 'alcohol__name', 'message'
    )
    readonly_fields = ('created_at', 'updated_at', 'purchaser', 'supplier', 'product', 'alcohol')
    # raw_id_fields = ('purchaser', 'supplier', 'product', 'alcohol') # Можно использовать для больших баз данных
    
    # Добавим действие для массовой отмены запросов
    actions = ['cancel_requests']

    def get_queryset(self, request):
        """Оптимизируем запросы с помощью select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('purchaser', 'supplier', 'product', 'alcohol')

    def get_item_name(self, obj):
        """Отображает имя продукта или алкоголя."""
        if obj.product:
            return obj.product.name
        elif obj.alcohol:
            return obj.alcohol.name
        return "Не указан"
    get_item_name.short_description = 'Товар'
    get_item_name.admin_order_field = 'product__name' # Позволяет сортировать по этому полю

    def purchaser_name(self, obj):
        """Отображает имя закупщика."""
        return obj.purchaser.get_full_name() or obj.purchaser.username
    purchaser_name.short_description = 'Закупщик'
    purchaser_name.admin_order_field = 'purchaser__username'

    def supplier_name(self, obj):
        """Отображает имя поставщика."""
        return obj.supplier.name
    supplier_name.short_description = 'Поставщик'
    supplier_name.admin_order_field = 'supplier__name'

    def has_add_permission(self, request):
        """
        Запрещает добавление через админку, так как это должно происходить через API.
        """
        return False # Или True, если администраторам нужно разрешить создание вручную

    def has_change_permission(self, request, obj=None):
        """
        Разрешает изменение только администраторам.
        """
        return request.user.role == 'admin'

    def has_delete_permission(self, request, obj=None):
        """
        Разрешает удаление только администраторам.
        """
        return request.user.role == 'admin'

    def cancel_requests(self, request, queryset):
        """
        Действие админки: отменить выбранные запросы.
        """
        updated_count = queryset.filter(status='pending').update(status='cancelled')
        self.message_user(
            request, 
            f"{updated_count} запрос(ов) успешно отменено."
        )
    cancel_requests.short_description = "Отменить выбранные запросы (ожидающие)"

# Регистрация всех моделей
admin.site.register(Organization)
admin.site.register(City)
admin.site.register(User, CustomUserAdmin)
admin.site.register(PurchaserProfile, PurchaserProfileAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(AlcoholProduct, AlcoholProductAdmin)
admin.site.register(Supplier, SupplierAdmin)
admin.site.register(SupplierToken, SupplierTokenAdmin)
admin.site.register(Price, PriceAdmin)
admin.site.register(PriceAlcohol, PriceAlcoholAdmin)
admin.site.register(PriceRequest, PriceRequestAdmin)