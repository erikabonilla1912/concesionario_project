from django.urls import path

from . import views

app_name = 'pagos'

urlpatterns = [
    path('', views.lista_facturas, name='lista_facturas'),
    path('nueva/', views.crear_factura, name='crear_factura'),
    path('<int:id>/', views.detalle_factura, name='detalle_factura'),
    path('<int:id>/imprimir/', views.imprimir_factura, name='imprimir_factura'),
    path('<int:id>/editar/', views.editar_factura, name='editar_factura'),
    path('<int:id>/anular/', views.anular_factura, name='anular_factura'),
    path('<int:id>/eliminar/', views.eliminar_factura, name='eliminar_factura'),

    path('<int:id>/items/nuevo/', views.agregar_item, name='agregar_item'),
    path('<int:id>/items/<int:indice>/editar/', views.editar_item, name='editar_item'),
    path('<int:id>/items/<int:indice>/eliminar/', views.eliminar_item, name='eliminar_item'),

    path('<int:id>/cuotas/generar/', views.generar_cuotas, name='generar_cuotas'),
    path('<int:id>/cuotas/<int:indice>/editar/', views.editar_cuota, name='editar_cuota'),
    path('<int:id>/cuotas/eliminar/', views.eliminar_cuotas, name='eliminar_cuotas'),

    path('<int:id>/pagos/nuevo/', views.registrar_pago, name='registrar_pago'),
    path('<int:id>/pagos/<int:indice>/', views.detalle_pago, name='detalle_pago'),
    path('<int:id>/pagos/<int:indice>/editar/', views.editar_pago, name='editar_pago'),
    path('<int:id>/pagos/<int:indice>/eliminar/', views.eliminar_pago, name='eliminar_pago'),
    path('pagos/', views.lista_pagos, name='lista_pagos'),
]
