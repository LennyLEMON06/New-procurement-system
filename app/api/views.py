# views.py
from rest_framework import viewsets, permissions, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import authenticate, login
from .models import Organization, City, User, PurchaserProfile, Product, AlcoholProduct, Supplier, Price, SupplierToken
from .serializers import (
    OrganizationSerializer, CitySerializer, UserSerializer, UserCreateSerializer,
    PurchaserProfileSerializer, ProductSerializer, AlcoholProductSerializer,
    SupplierSerializer, PriceSerializer, SupplierTokenSerializer
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

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

class AlcoholProductViewSet(viewsets.ModelViewSet):
    queryset = AlcoholProduct.objects.all()
    serializer_class = AlcoholProductSerializer
    permission_classes = [permissions.IsAuthenticated]

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