from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_facturas, name='lista_facturas'),
    path('nueva/<int:venta_pk>/', views.nueva_factura, name='nueva_factura'),
    path('detalle/<int:pk>/', views.detalle_factura, name='detalle_factura'),
    path('pago/nuevo/<int:factura_pk>/', views.nuevo_pago, name='nuevo_pago'),
]
