from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from gestion_usuarios.decorators import requiere_permiso
from .models import Mantenimiento, PropietarioAnterior
from clientes_vehiculos.models import Vehiculo

@requiere_permiso('historial')
def lista_historial(request):
    vehiculo_id = request.GET.get('vehiculo','')
    vehiculos = Vehiculo.objects.all()
    mantenimientos = Mantenimiento.objects.select_related('vehiculo').filter(vehiculo_id=vehiculo_id) if vehiculo_id else Mantenimiento.objects.select_related('vehiculo').all().order_by('-fecha')
    propietarios = PropietarioAnterior.objects.select_related('vehiculo').filter(vehiculo_id=vehiculo_id) if vehiculo_id else PropietarioAnterior.objects.select_related('vehiculo').all()
    return render(request, 'historial_vehiculo/lista_historial.html', {'mantenimientos': mantenimientos, 'propietarios': propietarios, 'vehiculos': vehiculos, 'vehiculo_id': vehiculo_id})

@requiere_permiso('historial')
def nuevo_mantenimiento(request):
    vehiculos = Vehiculo.objects.all()
    if request.method == 'POST':
        Mantenimiento.objects.create(
            vehiculo_id=request.POST['vehiculo'], tipo=request.POST['tipo'],
            descripcion=request.POST['descripcion'], fecha=request.POST['fecha'],
            costo=request.POST['costo']
        )
        messages.success(request, 'Mantenimiento registrado.')
        return redirect('lista_historial')
    return render(request, 'historial_vehiculo/form_mantenimiento.html', {'vehiculos': vehiculos})

@requiere_permiso('historial')
def nuevo_propietario(request):
    vehiculos = Vehiculo.objects.all()
    if request.method == 'POST':
        PropietarioAnterior.objects.create(
            vehiculo_id=request.POST['vehiculo'], nombre=request.POST['nombre'],
            fecha_inicio=request.POST['fecha_inicio'], fecha_fin=request.POST['fecha_fin']
        )
        messages.success(request, 'Propietario registrado.')
        return redirect('lista_historial')
    return render(request, 'historial_vehiculo/form_propietario.html', {'vehiculos': vehiculos})