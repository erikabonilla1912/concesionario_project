from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('login')),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('home/', include('gestion_usuarios.urls')),
    path('clientes/', include('clientes_vehiculos.urls')),
    path('ventas/', include('ventas_cotizaciones.urls')),
    path('historial/', include('historial_vehiculo.urls')),
    path('pagos/', include('pagos_facturacion.urls')),
]
