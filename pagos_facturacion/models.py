from djongo import models


class HorarioAtencion(models.Model):
    hora_apertura = models.CharField(max_length=5)
    hora_cierre = models.CharField(max_length=5)
    dias_habiles = models.JSONField(default=list)

    class Meta:
        abstract = True


class Politica(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    activa = models.BooleanField(default=True)

    class Meta:
        abstract = True


class RedSocial(models.Model):
    REDES = [
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('twitter', 'Twitter'),
        ('youtube', 'YouTube'),
        ('linkedin', 'LinkedIn'),
        ('tiktok', 'TikTok'),
    ]
    red = models.CharField(max_length=20, choices=REDES)
    url = models.URLField()

    class Meta:
        abstract = True


class Configuracion(models.Model):
    nombre_empresa = models.CharField(max_length=150)
    nit = models.CharField(max_length=20, blank=True)
    direccion = models.TextField(blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    sitio_web = models.URLField(blank=True)
    porcentaje_iva = models.FloatField(default=19.0)
    moneda = models.CharField(max_length=10, default='COP')
    horario_atencion = models.EmbeddedField(
        model_container=HorarioAtencion,
        null=True,
        blank=True
    )
    politicas = models.ArrayField(model_container=Politica, blank=True)
    redes_sociales = models.ArrayField(model_container=RedSocial, blank=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'configuracion'

    def __str__(self):
        return self.nombre_empresa
