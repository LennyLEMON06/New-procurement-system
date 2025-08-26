# your_app/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'organizations', views.OrganizationViewSet)
router.register(r'cities', views.CityViewSet)
router.register(r'users', views.UserViewSet)
router.register(r'purchaser-profiles', views.PurchaserProfileViewSet)
router.register(r'products', views.ProductViewSet)
router.register(r'alcohol-products', views.AlcoholProductViewSet)
router.register(r'suppliers', views.SupplierViewSet)
router.register(r'prices', views.PriceViewSet)

urlpatterns = [
    path('', include(router.urls)),
]