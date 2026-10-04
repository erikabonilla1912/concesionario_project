from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Rol, PerfilUsuario
from .decorators import solo_admin, requiere_permiso
from clientes_vehiculos.models import Cliente, Vehiculo
from ventas_cotizaciones.models import Venta

MODULOS_PERMISOS = [
    ('perm_clientes',  'Clientes y Vehículos'),
    ('perm_ventas',    'Ventas y Cotizaciones'),
    ('perm_historial', 'Historial del Vehículo'),
    ('perm_pagos',     'Pagos y Facturación'),
    ('perm_usuarios',  'Gestión de Usuarios y Roles'),
]

@login_required
def home(request):
    context = {
        'total_clientes': Cliente.objects.count(),
        'total_vehiculos': Vehiculo.objects.count(),
        'total_ventas': Venta.objects.count(),
        'vehiculos_disponibles': Vehiculo.objects.filter(estado='disponible').count(),
    }
    return render(request, 'gestion_usuarios/home.html', context)

@solo_admin
def lista_usuarios(request):
    usuarios = User.objects.select_related('perfil', 'perfil__rol').all().order_by('username')
    return render(request, 'gestion_usuarios/lista_usuarios.html', {'usuarios': usuarios})

@solo_admin
def nuevo_usuario(request):
    roles = Rol.objects.all()
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        email = request.POST.get('email', '')
        rol_id = request.POST.get('rol')
        telefono = request.POST.get('telefono', '')
        if User.objects.filter(username=username).exists():
            messages.error(request, 'El usuario ya existe.')
        else:
            u = User.objects.create_user(username=username, password=password,
                first_name=first_name, last_name=last_name, email=email)
            rol = Rol.objects.get(pk=rol_id) if rol_id else None
            PerfilUsuario.objects.create(usuario=u, rol=rol, telefono=telefono)
            messages.success(request, f'Usuario {username} creado exitosamente.')
            return redirect('lista_usuarios')
    return render(request, 'gestion_usuarios/form_usuario.html', {'roles': roles, 'accion': 'Nuevo'})

@solo_admin
def editar_usuario(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    roles = Rol.objects.all()
    perfil, _ = PerfilUsuario.objects.get_or_create(usuario=usuario)
    if request.method == 'POST':
        usuario.first_name = request.POST.get('first_name', '')
        usuario.last_name = request.POST.get('last_name', '')
        usuario.email = request.POST.get('email', '')
        usuario.save()
        rol_id = request.POST.get('rol')
        perfil.rol = Rol.objects.get(pk=rol_id) if rol_id else None
        perfil.telefono = request.POST.get('telefono', '')
        perfil.save()
        messages.success(request, 'Usuario actualizado.')
        return redirect('lista_usuarios')
    return render(request, 'gestion_usuarios/form_usuario.html',
                  {'usuario': usuario, 'perfil': perfil, 'roles': roles, 'accion': 'Editar'})

@solo_admin
def eliminar_usuario(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        usuario.delete()
        messages.success(request, 'Usuario eliminado.')
        return redirect('lista_usuarios')
    return render(request, 'gestion_usuarios/confirmar_eliminar.html',
                  {'objeto': usuario, 'tipo': 'usuario'})

@solo_admin
def lista_roles(request):
    roles = Rol.objects.all()
    return render(request, 'gestion_usuarios/lista_roles.html', {'roles': roles})

@solo_admin
def nuevo_rol(request):
    if request.method == 'POST':
        nombre = request.POST['nombre']
        descripcion = request.POST.get('descripcion', '')
        rol = Rol.objects.create(nombre=nombre, descripcion=descripcion)
        # Guardar permisos
        for campo, _ in MODULOS_PERMISOS:
            setattr(rol, campo, campo in request.POST)
        rol.save()
        messages.success(request, f'Rol "{nombre}" creado.')
        return redirect('lista_roles')
    return render(request, 'gestion_usuarios/form_rol.html', {'modulos': MODULOS_PERMISOS})

@solo_admin
def editar_rol(request, pk):
    rol = get_object_or_404(Rol, pk=pk)
    if request.method == 'POST':
        rol.nombre = request.POST['nombre']
        rol.descripcion = request.POST.get('descripcion', '')
        for campo, _ in MODULOS_PERMISOS:
            setattr(rol, campo, campo in request.POST)
        rol.save()
        messages.success(request, f'Rol "{rol.nombre}" actualizado.')
        return redirect('lista_roles')
    return render(request, 'gestion_usuarios/form_rol.html',
                  {'rol': rol, 'modulos': MODULOS_PERMISOS})

@solo_admin
def eliminar_rol(request, pk):
    rol = get_object_or_404(Rol, pk=pk)
    if request.method == 'POST':
        rol.delete()
        messages.success(request, 'Rol eliminado.')
        return redirect('lista_roles')
    return render(request, 'gestion_usuarios/confirmar_eliminar.html',
                  {'objeto': rol, 'tipo': 'rol'})