# views.py
from rest_framework import viewsets, permissions, generics
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth import authenticate, login
from django.db.models import Prefetch
from .models import Organization, City, User, PurchaserProfile, Product, AlcoholProduct, Supplier, Price, SupplierToken, PriceAlcohol, PriceRequest
from .permissions import IsPurchaserOrHigher, IsAdminOrStaff # Импорт разрешений
from .serializers import (
    OrganizationSerializer, CitySerializer, UserSerializer, UserCreateSerializer,
    PurchaserProfileSerializer, ProductSerializer, AlcoholProductSerializer,
    SupplierSerializer, PriceSerializer, PriceRequestSerializer, ProductWithPricesSerializer,
    AlcoholProductWithPricesSerializer, SupplierPriceSerializer, SupplierPriceAlcoholSerializer
)

class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]

class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    permission_classes = [permissions.IsAuthenticated]

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

class PurchaserProfileViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PurchaserProfile.objects.all()
    serializer_class = PurchaserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

# Модифицируем существующие ViewSet'ы для продуктов и алкоголя
class ProductViewSet(viewsets.ModelViewSet): # Сделаем только для чтения, если не нужно редактирование через API
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsPurchaserOrHigher] # Используем новое разрешение

    def get_queryset(self):
        """
        Фильтруем продукты в зависимости от роли пользователя.
        """
        user = self.request.user
        if user.role == 'admin':
            return Product.objects.all()
        elif hasattr(user, 'purchaser_profile'):
            profile = user.purchaser_profile
            orgs = profile.organizations.all()
            cities = profile.cities.all()
            # Продукты из разрешенных организаций
            return Product.objects.filter(organization__in=orgs)
        else:
            # Если у пользователя нет профиля закупщика, но он имеет роль purchaser/chief_purchaser
            # Можно вернуть пустой queryset или обработать иначе
            return Product.objects.none()
            
    @action(detail=False, methods=['get'], url_path='with-prices')
    def with_prices(self, request):
        """
        Возвращает список продуктов с ценами от поставщиков.
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        # Предзагрузка цен для оптимизации
        queryset = queryset.prefetch_related(
            Prefetch('price_set', queryset=Price.objects.select_related('supplier'))
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ProductWithPricesSerializer(page, many=True, context=self.get_serializer_context())
            return self.get_paginated_response(serializer.data)

        serializer = ProductWithPricesSerializer(queryset, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

class AlcoholProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AlcoholProduct.objects.all()
    serializer_class = AlcoholProductSerializer
    permission_classes = [IsPurchaserOrHigher]

    def get_queryset(self):
        """
        Фильтруем алкогольные продукты в зависимости от роли пользователя.
        """
        user = self.request.user
        if user.role == 'admin':
            return AlcoholProduct.objects.all()
        elif hasattr(user, 'purchaser_profile'):
            profile = user.purchaser_profile
            orgs = profile.organizations.all()
            # Алкоголь из разрешенных организаций
            return AlcoholProduct.objects.filter(organization__in=orgs)
        else:
            return AlcoholProduct.objects.none()
            
    @action(detail=False, methods=['get'], url_path='with-prices')
    def with_prices(self, request):
        """
        Возвращает список алкогольных продуктов с ценами от поставщиков.
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        # Предзагрузка цен
        queryset = queryset.prefetch_related(
            Prefetch('pricealcohol_set', queryset=PriceAlcohol.objects.select_related('supplier'))
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = AlcoholProductWithPricesSerializer(page, many=True, context=self.get_serializer_context())
            return self.get_paginated_response(serializer.data)

        serializer = AlcoholProductWithPricesSerializer(queryset, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['get'], permission_classes=[])
    def token(self, request, pk=None):
        supplier = self.get_object()
        token = SupplierToken.get_or_create_token(supplier)
        return Response({'token': str(token)})

class PriceViewSet(viewsets.ModelViewSet):
    queryset = Price.objects.all()
    serializer_class = PriceSerializer
    permission_classes = [permissions.IsAuthenticated]

# Добавим ViewSet для получения цен по конкретному продукту/алкоголю
class ProductPriceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SupplierPriceSerializer
    permission_classes = [IsPurchaserOrHigher]
    
    def get_queryset(self):
        """
        Возвращает цены на конкретный продукт, доступные пользователю.
        """
        user = self.request.user
        product_pk = self.kwargs.get('product_pk')
        
        if not product_pk:
            return Price.objects.none()
            
        try:
            product = Product.objects.get(pk=product_pk)
        except Product.DoesNotExist:
            return Price.objects.none()
            
        # Проверка доступа к продукту
        if user.role == 'admin':
            return Price.objects.filter(product=product)
        elif hasattr(user, 'purchaser_profile'):
            profile = user.purchaser_profile
            if product.organization in profile.organizations.all():
                return Price.objects.filter(product=product)
                
        return Price.objects.none()

class AlcoholPriceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SupplierPriceAlcoholSerializer
    permission_classes = [IsPurchaserOrHigher]
    
    def get_queryset(self):
        """
        Возвращает цены на конкретный алкогольный продукт, доступные пользователю.
        """
        user = self.request.user
        alcohol_pk = self.kwargs.get('alcohol_pk')
        
        if not alcohol_pk:
            return PriceAlcohol.objects.none()
            
        try:
            alcohol = AlcoholProduct.objects.get(pk=alcohol_pk)
        except AlcoholProduct.DoesNotExist:
            return PriceAlcohol.objects.none()
            
        # Проверка доступа к алкоголю
        if user.role == 'admin':
            return PriceAlcohol.objects.filter(alcohol=alcohol)
        elif hasattr(user, 'purchaser_profile'):
            profile = user.purchaser_profile
            if alcohol.organization in profile.organizations.all():
                return PriceAlcohol.objects.filter(alcohol=alcohol)
                
        return PriceAlcohol.objects.none()
    
class PriceRequestViewSet(viewsets.ModelViewSet):
    queryset = PriceRequest.objects.all()
    serializer_class = PriceRequestSerializer
    permission_classes = [permissions.IsAuthenticated] # Используем базовое разрешение, логика фильтрации внутри
    
    def get_queryset(self):
        """
        Фильтруем запросы в зависимости от роли пользователя.
        """
        user = self.request.user
        if user.role == 'admin':
            return PriceRequest.objects.all()
        elif user.role in ['chief_purchaser', 'purchaser']:
            # Закупщики видят только свои запросы
            return PriceRequest.objects.filter(purchaser=user)
        else:
            # На всякий случай, если роль не определена
            return PriceRequest.objects.none()
            
    def perform_create(self, serializer):
        """
        Автоматически устанавливаем закупщика при создании запроса.
        """
        serializer.save(purchaser=self.request.user)
        
    def update(self, request, *args, **kwargs):
        """
        Запрещаем обновление некоторых полей для обычных пользователей.
        """
        instance = self.get_object()
        user = request.user
        
        # Только администраторы могут изменять закупщика и даты
        if user.role != 'admin':
            if 'purchaser' in request.data:
                return Response(
                    {"error": "Вы не можете изменить закупщика."}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            # Можно добавить проверки на изменение created_at, updated_at если нужно
                
        return super().update(request, *args, **kwargs)
        
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def cancel(self, request, pk=None):
        """
        Действие для отмены запроса.
        """
        price_request = self.get_object()
        user = request.user
        
        # Проверка прав: только владелец или админ может отменить
        if user.role == 'admin' or price_request.purchaser == user:
            if price_request.status == 'pending':
                price_request.status = 'cancelled'
                price_request.save()
                return Response({'status': 'Запрос отменен'}, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': 'Запрос не может быть отменен, так как он уже обработан.'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                {'error': 'У вас нет прав для отмены этого запроса.'}, 
                status=status.HTTP_403_FORBIDDEN
            )