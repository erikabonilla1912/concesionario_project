from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def requiere_permiso(modulo):
    """
    Decorador que verifica si el usuario tiene permiso para acceder a un módulo.
    Uso: @requiere_permiso('clientes')
    Módulos disponibles: clientes, ventas, historial, pagos, usuarios
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            try:
                perfil = request.user.perfil
            except Exception:
                messages.error(request, 'Tu usuario no tiene perfil asignado. Contacta al administrador.')
                return redirect('home')
            if not perfil.tiene_permiso(modulo):
                messages.error(request, 'No tienes permiso para acceder a ese módulo.')
                return redirect('home')
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator

def solo_admin(view_func):
    """
    Decorador que solo permite acceso a administradores.
    """
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        try:
            perfil = request.user.perfil
        except Exception:
            messages.error(request, 'Tu usuario no tiene perfil asignado.')
            return redirect('home')
        if not perfil.es_admin():
            messages.error(request, 'Solo los administradores pueden acceder a esta sección.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped