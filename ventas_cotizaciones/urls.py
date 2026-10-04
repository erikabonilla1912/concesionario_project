from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_cotizaciones, name='lista_cotizaciones'),
    path('nueva/', views.nueva_cotizacion, name='nueva_cotizacion'),
    path('editar/<int:pk>/', views.editar_cotizacion, name='editar_cotizacion'),
    path('ventas/', views.lista_ventas, name='lista_ventas'),
    path('ventas/nueva/<int:cotizacion_pk>/', views.nueva_venta, name='nueva_venta'),
]
