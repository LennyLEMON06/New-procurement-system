from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
import uuid
from datetime import timedelta
from django.utils.timezone import now
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

class Organization(models.Model):
    name = models.CharField(
        max_length=255, 
        verbose_name="Название организации")
    description = models.TextField(
        blank=True, null=True, 
        verbose_name="Описание")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Организация'
        verbose_name_plural = 'Организации'

class City(models.Model):
    name = models.CharField(
        max_length=255, verbose_name="Город")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Город'
        verbose_name_plural = 'Города'

class User(AbstractUser):
    ROLES = (
        ('admin', 'Администратор'),
        ('chief_purchaser', 'Главный закупщик'),
        ('purchaser', 'Закупщик'),
    )
    role = models.CharField(
        max_length=20, 
        choices=ROLES, 
        verbose_name="Роль")
    phone_validator = RegexValidator(
        regex=r'^\+?1?\d{9,15}$', 
        message="Неверный формат номера телефона")
    phone = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        verbose_name="Телефон",
        validators=[phone_validator])

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

class PurchaserProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, 
        related_name='purchaser_profile')
    organizations = models.ManyToManyField(
        Organization, blank=True, 
        verbose_name="Доступные организации")
    cities = models.ManyToManyField(
        City, blank=True, 
        verbose_name="Доступные города")

    def __str__(self):
        return f"Профиль {self.user.username}"

    class Meta:
        verbose_name = 'Профиль закупщика'
        verbose_name_plural = 'Профили закупщиков'

class Product(models.Model):
    PRODUCT_TYPE = (
        ('boevka', 'Напитки Боевка'),
        ('grocery', 'Бакалея'),
        ('desserts', 'Десерты'),
        ('ice', 'Заморозка ММ'),
        ('milk', 'Молочка'),
        ('sh', 'СХ'),
        ('other', 'Другое'),
    )
    name = models.CharField(
        max_length=255, 
        verbose_name=u"Наименование")
    quantity = models.IntegerField(
        default=0, 
        validators=[MinValueValidator(0)], 
        verbose_name=u"Количество в месяц")  # (по умолчанию 0)
    unit = models.CharField(
        max_length=50, 
        verbose_name=u"Единица измерения")
    type = models.CharField(
        max_length=20, 
        choices=PRODUCT_TYPE, 
        verbose_name="Тип", 
        default='other')
    last_updated = models.DateTimeField(
        auto_now=True)
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, 
        verbose_name="Организация")

    def clean(self):
        super().clean()
        if self.quantity is not None and self.quantity < 0:
            raise ValidationError({"quantity": "Количество не может быть отрицательным"})
        if not self.name or not self.name.strip():
            raise ValidationError({"name": "Название не может быть пустым"})
    
    def save(self, *args, **kwargs):
        self.full_clean()  # Вызывает валидацию
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.organization} - {self.name}"
    
    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'

class AlcoholProduct(models.Model):
    name = models.CharField(
        max_length=255, 
        verbose_name=u"Наименование")
    quantity = models.IntegerField(
        default=0, validators=[MinValueValidator(0)], 
        verbose_name=u"Количество в месяц")
    unit = models.CharField(
        max_length=50, 
        verbose_name=u"Единица измерения")
    last_updated = models.DateTimeField(auto_now=True)
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, 
        verbose_name="Организация")
    excise_stamp_required = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Алкоголь'
        verbose_name_plural = 'Алкоголь'

    def clean(self):
        super().clean()
        if self.quantity is not None and self.quantity < 0:
            raise ValidationError({"quantity": "Количество не может быть отрицательным"})
        if not self.name or not self.name.strip():
            raise ValidationError({"name": "Название не может быть пустым"})


class Supplier(models.Model):
    SUPPLIER_TYPE = (
        ('prod', 'Продукты'),
        ('alco', 'Алкоголь'),
        ('all', 'Универсальный'),
    )
    name = models.CharField(
        max_length=255, 
        verbose_name=u"Наименование")
    contact_info = models.TextField(verbose_name=u"Контактная информация")
    inn_validator = RegexValidator(
        regex=r'^\d{10,12}$', 
        message="Неверный формат ИНН")
    inn = models.CharField(
        max_length=12, verbose_name="ИНН", 
        validators=[inn_validator])
    type = models.CharField(
        max_length=20, choices=SUPPLIER_TYPE, 
        verbose_name="Тип", default='prod')
    city = models.ForeignKey(
        City, on_delete=models.SET_NULL, 
        null=True, blank=True, 
        verbose_name="Город")
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, 
        verbose_name="Организация")

    def __str__(self):
        return f"{self.organization} - {self.name}"
    
    class Meta:
        verbose_name = 'Поставщик'
        verbose_name_plural = 'Поставщики'

class SupplierToken(models.Model):
    supplier = models.ForeignKey(
        Supplier, on_delete=models.CASCADE, 
        verbose_name="Наименование поставщика")
    token = models.UUIDField(
        default=uuid.uuid4, unique=True, 
        verbose_name="Токен")
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Создан")

    def is_expired(self): # Обновленный метод
        # Проверяем, что created_at не None перед выполнением операций
        if self.created_at is None:
            # Если дата создания не установлена, считаем токен "истекшим" или недействительным
            # Это может быть полезно для объектов, которые еще не были сохранены
            return True # Или False, в зависимости от вашей логики. True, если считаем, что неактивный токен "истек".
        return now() > self.created_at + timedelta(hours=24)

    @classmethod
    def get_or_create_token(cls, supplier):
        token_obj, created = cls.objects.get_or_create(supplier=supplier)
        if not created and token_obj.is_expired():
            token_obj.token = uuid.uuid4()
            token_obj.created_at = now()
            token_obj.save()
        return token_obj.token
    
    class Meta:
        verbose_name = 'Токен поставщика'
        verbose_name_plural = 'Токен поставщиков'

class Price(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, 
        verbose_name="Продукт")
    supplier = models.ForeignKey(
        Supplier, on_delete=models.CASCADE, 
        verbose_name="Поставщик")
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, blank=True, 
        verbose_name="Предложенная цена",
        validators=[MinValueValidator(0)]
    )
    manufacturer = models.CharField(
        max_length=255, 
        blank=True, null=True, 
        verbose_name="Единица измерения")
    date_added = models.DateTimeField(
        default=timezone.now, 
        verbose_name="Дата добавления")
    date_updated = models.DateTimeField(
        auto_now=True, 
        verbose_name="Дата обновления")

    def __str__(self):
        return f"{self.product.name} - {self.supplier.name} - {self.price} - {self.date_added}"

    class Meta:
        unique_together = ('product', 'supplier', 'date_added')
        verbose_name = 'Предложения от поставщиков по продукту'
        verbose_name_plural = 'Предложения от поставщиков по продуктам'

    def save(self, *args, **kwargs):
        self.date_updated = timezone.now()
        super().save(*args, **kwargs)

    def clean(self):
        if self.price and self.price > 99999999.99:
            raise ValidationError("Цена слишком высока")

class PriceAlcohol(models.Model):
    alcohol = models.ForeignKey(
        AlcoholProduct, on_delete=models.CASCADE, 
        verbose_name="Алкоголь")
    supplier = models.ForeignKey(
        Supplier, on_delete=models.CASCADE, 
        verbose_name="Поставщик")
    price = models.DecimalField(
        max_digits=10, decimal_places=2, 
        null=True, blank=True, 
        verbose_name="Предложенная цена")
    manufacturer = models.CharField(
        max_length=255, blank=True, null=True, 
        verbose_name="Единица измерения")
    date_added = models.DateTimeField(
        default=timezone.now, 
        verbose_name="Дата добавления")
    date_updated = models.DateTimeField(
        auto_now=True, 
        verbose_name="Дата обновления")

    def __str__(self):
        return f"{self.alcohol.name} - {self.supplier.name} - {self.price} - {self.date_added}"

    class Meta:
        unique_together = ('alcohol', 'supplier', 'date_added') # убираем unique_together
        verbose_name = 'Предложения от поставщиков по алкоголю'
        verbose_name_plural = 'Предложения от поставщиков по алкоголю'

    def save(self, *args, **kwargs):
        self.date_updated = timezone.now()
        super().save(*args, **kwargs)