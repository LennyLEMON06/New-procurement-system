# your_app/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Добавим дополнительные роутеры для вложенных ресурсов
from rest_framework_nested import routers

router = DefaultRouter()
router.register(r'organizations', views.OrganizationViewSet)
router.register(r'cities', views.CityViewSet)
router.register(r'users', views.UserViewSet)
router.register(r'purchaser-profiles', views.PurchaserProfileViewSet)
router.register(r'products', views.ProductViewSet)
router.register(r'alcohol-products', views.AlcoholProductViewSet)
router.register(r'suppliers', views.SupplierViewSet)
router.register(r'prices', views.PriceViewSet)
router.register(r'price-requests', views.PriceRequestViewSet)

urlpatterns = [
    path('', include(router.urls)),
]


# Создаем вложенный роутер для цен по продуктам
products_router = routers.NestedSimpleRouter(router, r'products', lookup='product')
products_router.register(r'prices', views.ProductPriceViewSet, basename='product-prices')

# Создаем вложенный роутер для цен по алкоголю
alcohol_router = routers.NestedSimpleRouter(router, r'alcohol-products', lookup='alcohol')
alcohol_router.register(r'prices', views.AlcoholPriceViewSet, basename='alcohol-prices')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(products_router.urls)), # Включаем вложенные URL
    path('', include(alcohol_router.urls)),  # Включаем вложенные URL
]