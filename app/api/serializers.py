from rest_framework import serializers
from .models import Organization, City, User, PurchaserProfile, Product, AlcoholProduct, Supplier, Price, SupplierToken

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
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'role', 'phone']

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'first_name', 'last_name', 'email', 'role', 'phone']

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

class PurchaserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    organizations = OrganizationSerializer(many=True)
    cities = CitySerializer(many=True)

    class Meta:
        model = PurchaserProfile
        fields = '__all__'

# Продукты
class ProductSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)

    class Meta:
        model = Product
        fields = '__all__'

class AlcoholProductSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)

    class Meta:
        model = AlcoholProduct
        fields = '__all__'

# Поставщики
class SupplierSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source='city.name', read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)

    class Meta:
        model = Supplier
        fields = '__all__'

class SupplierTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierToken
        fields = ['token', 'created_at']

# Цены
class PriceSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)

    class Meta:
        model = Price
        fields = '__all__'
        read_only_fields = ['date_added', 'date_updated']