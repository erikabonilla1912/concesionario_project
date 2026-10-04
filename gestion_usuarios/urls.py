from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('usuarios/nuevo/', views.nuevo_usuario, name='nuevo_usuario'),
    path('usuarios/editar/<int:pk>/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/eliminar/<int:pk>/', views.eliminar_usuario, name='eliminar_usuario'),
    path('roles/', views.lista_roles, name='lista_roles'),
    path('roles/nuevo/', views.nuevo_rol, name='nuevo_rol'),
    path('roles/editar/<int:pk>/', views.editar_rol, name='editar_rol'),
    path('roles/eliminar/<int:pk>/', views.eliminar_rol, name='eliminar_rol'),
]