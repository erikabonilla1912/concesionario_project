from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from gestion_usuarios.decorators import requiere_permiso
from .models import Cotizacion, Venta
from clientes_vehiculos.models import Cliente, Vehiculo

@requiere_permiso('ventas')
def lista_cotizaciones(request):
    cotizaciones = Cotizacion.objects.select_related(
        'cliente', 'vehiculo', 'vendedor'
    ).prefetch_related('venta__factura').all().order_by('-fecha')

    # Anotar cada cotización con flags útiles para el template
    for c in cotizaciones:
        try:
            venta = c.venta
            c.tiene_venta = True
            try:
                c.tiene_factura = True
                c.factura_pk = venta.factura.pk
            except Exception:
                c.tiene_factura = False
                c.factura_pk = None
        except Exception:
            c.tiene_venta = False
            c.tiene_factura = False
            c.factura_pk = None

    return render(request, 'ventas_cotizaciones/lista_cotizaciones.html', {'cotizaciones': cotizaciones})

@requiere_permiso('ventas')
def nueva_cotizacion(request):
    clientes = Cliente.objects.all()
    vehiculos = Vehiculo.objects.filter(estado='disponible')
    if request.method == 'POST':
        Cotizacion.objects.create(
            cliente_id=request.POST['cliente'],
            vehiculo_id=request.POST['vehiculo'],
            vendedor=request.user,
            precio_ofertado=request.POST['precio_ofertado'],
            notas=request.POST.get('notas', ''),
            estado='pendiente'
        )
        messages.success(request, 'Cotización creada exitosamente.')
        return redirect('lista_cotizaciones')
    return render(request, 'ventas_cotizaciones/form_cotizacion.html', {
        'clientes': clientes, 'vehiculos': vehiculos, 'accion': 'Nueva'
    })

@requiere_permiso('ventas')
def editar_cotizacion(request, pk):
    cotizacion = get_object_or_404(Cotizacion, pk=pk)
    if request.method == 'POST':
        cotizacion.estado = request.POST['estado']
        cotizacion.precio_ofertado = request.POST['precio_ofertado']
        cotizacion.notas = request.POST.get('notas', '')
        cotizacion.save()
        messages.success(request, 'Cotización actualizada.')
        return redirect('lista_cotizaciones')
    return render(request, 'ventas_cotizaciones/form_cotizacion.html', {
        'cotizacion': cotizacion, 'accion': 'Editar'
    })

@requiere_permiso('ventas')
def lista_ventas(request):
    ventas = Venta.objects.select_related(
        'cotizacion__cliente', 'cotizacion__vehiculo'
    ).prefetch_related('factura').all().order_by('-fecha_venta')
    return render(request, 'ventas_cotizaciones/lista_ventas.html', {'ventas': ventas})

@requiere_permiso('ventas')
def nueva_venta(request, cotizacion_pk):
    cotizacion = get_object_or_404(Cotizacion, pk=cotizacion_pk)
    if request.method == 'POST':
        Venta.objects.create(
            cotizacion=cotizacion,
            precio_final=request.POST['precio_final'],
            forma_pago=request.POST['forma_pago']
        )
        cotizacion.estado = 'aprobada'
        cotizacion.save()
        cotizacion.vehiculo.estado = 'vendido'
        cotizacion.vehiculo.save()
        messages.success(request, 'Venta registrada exitosamente.')
        return redirect('lista_ventas')
    return render(request, 'ventas_cotizaciones/form_venta.html', {'cotizacion': cotizacion})