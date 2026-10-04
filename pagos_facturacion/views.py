from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from gestion_usuarios.decorators import requiere_permiso
from .models import Factura, Pago
from ventas_cotizaciones.models import Venta

@requiere_permiso('pagos')
def lista_facturas(request):
    facturas = Factura.objects.select_related('venta__cotizacion__cliente').all().order_by('-fecha_emision')
    return render(request, 'pagos_facturacion/lista_facturas.html', {'facturas': facturas})

@requiere_permiso('pagos')
def nueva_factura(request, venta_pk):
    venta = get_object_or_404(Venta, pk=venta_pk)
    if request.method == 'POST':
        subtotal = float(request.POST['subtotal'])
        impuesto = subtotal * 0.19
        total = subtotal + impuesto
        import random, string
        numero = 'FAC-' + ''.join(random.choices(string.digits, k=6))
        Factura.objects.create(venta=venta, numero_factura=numero, subtotal=subtotal, impuesto=round(impuesto,2), total=round(total,2))
        messages.success(request, f'Factura {numero} generada.')
        return redirect('lista_facturas')
    return render(request, 'pagos_facturacion/form_factura.html', {'venta': venta})

@requiere_permiso('pagos')
def detalle_factura(request, pk):
    factura = get_object_or_404(Factura, pk=pk)
    pagos = factura.pagos.all()
    return render(request, 'pagos_facturacion/detalle_factura.html', {'factura': factura, 'pagos': pagos})

@requiere_permiso('pagos')
def nuevo_pago(request, factura_pk):
    factura = get_object_or_404(Factura, pk=factura_pk)
    if request.method == 'POST':
        Pago.objects.create(
            factura=factura, tipo=request.POST['tipo'],
            monto=request.POST['monto'], numero_cuota=request.POST.get('numero_cuota') or None
        )
        messages.success(request, 'Pago registrado.')
        return redirect('detalle_factura', pk=factura_pk)
    return render(request, 'pagos_facturacion/form_pago.html', {'factura': factura})