from rest_framework import serializers
from .models import (
    Organization, City, User, PurchaserProfile, 
    Product, AlcoholProduct, Supplier, Price, 
    SupplierToken, PriceAlcohol, PriceRequest
)
# Простые модели
class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = '__all__'

class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 
                  'first_name', 'last_name', 
                  'email', 'role', 'phone']

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password', 
                  'first_name', 'last_name', 
                  'email', 'role', 'phone']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            email=validated_data.get('email', ''),
            role=validated_data.get('role', 'purchaser'),
            phone=validated_data.get('phone', '')
        )
        return user

# Профиль закупщика
class PurchaserProfileSerializer(serializers.ModelSerializer):
    # Для чтения - вложенные сериализаторы
    user = UserSerializer(read_only=True)
    organizations = OrganizationSerializer(many=True, read_only=True)
    cities = CitySerializer(many=True, read_only=True)

    # Для записи - ID
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source='user', 
        write_only=True
    )
    organization_ids = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all(), 
        source='organizations', 
        write_only=True,
        many=True
    )
    city_ids = serializers.PrimaryKeyRelatedField(
        queryset=City.objects.all(), 
        source='cities', 
        write_only=True,
        many=True
    )

    class Meta:
        model = PurchaserProfile
        fields = '__all__'

# Продукты
class ProductSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', 
                                              read_only=True)

    class Meta:
        model = Product
        fields = '__all__'

class AlcoholProductSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', 
                                              read_only=True)

    class Meta:
        model = AlcoholProduct
        fields = '__all__'

# Поставщики
class SupplierSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source='city.name', read_only=True)
    organization_name = serializers.CharField(source='organization.name', 
                                              read_only=True)

    class Meta:
        model = Supplier
        fields = '__all__'

class SupplierTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierToken
        fields = ['token', 'created_at']

# Цены
class PriceSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', 
                                         read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', 
                                          read_only=True)

    class Meta:
        model = Price
        fields = '__all__'
        read_only_fields = ['date_added', 'date_updated']

# Новый сериализатор для отображения цен поставщиков для конкретного продукта
class SupplierPriceSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.name', 
                                          read_only=True)
    supplier_id = serializers.IntegerField(source='supplier.id', 
                                           read_only=True)
    
    class Meta:
        model = Price
        fields = ['id', 'price', 'manufacturer', 
                  'date_updated', 'supplier_name', 'supplier_id']

class SupplierPriceAlcoholSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.name', 
                                          read_only=True)
    supplier_id = serializers.IntegerField(source='supplier.id', 
                                           read_only=True)
    
    class Meta:
        model = PriceAlcohol
        fields = ['id', 'price', 'manufacturer', 
                  'date_updated', 'supplier_name', 'supplier_id']

# Расширим существующие сериализаторы продуктов для включения цен
class ProductWithPricesSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', 
                                              read_only=True)
    prices = serializers.SerializerMethodField() # Динамически получаем цены
    
    class Meta:
        model = Product
        fields = '__all__' # Или перечислите конкретные поля + 'prices'
        
    def get_prices(self, obj):
        # Получаем цены для текущего продукта
        prices = Price.objects.filter(product=obj)
        # Фильтрация по организациям и городам пользователя будет в view
        serializer = SupplierPriceSerializer(prices, many=True)
        return serializer.data

class AlcoholProductWithPricesSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', 
                                              read_only=True)
    prices = serializers.SerializerMethodField()
    
    class Meta:
        model = AlcoholProduct
        fields = '__all__'
        
    def get_prices(self, obj):
        prices = PriceAlcohol.objects.filter(alcohol=obj)
        serializer = SupplierPriceAlcoholSerializer(prices, many=True)
        return serializer.data
    
class PriceRequestSerializer(serializers.ModelSerializer):
    purchaser_name = serializers.CharField(source='purchaser.get_full_name', 
                                           read_only=True)
    purchaser_username = serializers.CharField(source='purchaser.username', 
                                               read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', 
                                          read_only=True)
    product_name = serializers.CharField(source='product.name', 
                                         read_only=True, allow_null=True)
    alcohol_name = serializers.CharField(source='alcohol.name', 
                                         read_only=True, allow_null=True)
    item_name = serializers.SerializerMethodField() # Поле для отображения имени продукта или алкоголя
    
    class Meta:
        model = PriceRequest
        fields = '__all__'
        read_only_fields = ['purchaser', 'created_at', 'updated_at'] # purchaser будет устанавливаться в ViewSet
        
    def get_item_name(self, obj):
        """Возвращает имя продукта или алкоголя."""
        if obj.product:
            return obj.product.name
        elif obj.alcohol:
            return obj.alcohol.name
        return "Не указан"
        
    def validate(self, data):
        """
        Проверка на уровне сериализатора: должен быть указан product или alcohol, но не оба.
        """
        product = data.get('product')
        alcohol = data.get('alcohol')
        
        if not product and not alcohol:
            raise serializers.ValidationError("Необходимо указать либо продукт, либо алкоголь.")
        if product and alcohol:
            raise serializers.ValidationError("Можно запросить цену либо на продукт, либо на алкоголь, но не на оба одновременно.")
            
        return data