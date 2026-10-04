from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_clientes, name='lista_clientes'),
    path('nuevo/', views.nuevo_cliente, name='nuevo_cliente'),
    path('editar/<int:pk>/', views.editar_cliente, name='editar_cliente'),
    path('eliminar/<int:pk>/', views.eliminar_cliente, name='eliminar_cliente'),
    path('vehiculos/', views.lista_vehiculos, name='lista_vehiculos'),
    path('vehiculos/nuevo/', views.nuevo_vehiculo, name='nuevo_vehiculo'),
    path('vehiculos/editar/<int:pk>/', views.editar_vehiculo, name='editar_vehiculo'),
    path('vehiculos/eliminar/<int:pk>/', views.eliminar_vehiculo, name='eliminar_vehiculo'),
]
