from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_historial, name='lista_historial'),
    path('mantenimiento/nuevo/', views.nuevo_mantenimiento, name='nuevo_mantenimiento'),
    path('propietario/nuevo/', views.nuevo_propietario, name='nuevo_propietario'),
]
