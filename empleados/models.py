from django.db import models

# Definir una tupla con los valores del select tipo
tipos = (("Producto", "Producto"), ("Servicio", "Servicio"))


class Empleado(models.Model):
    producto_servicio = models.CharField(max_length=200)
    descripcion = models.CharField(max_length=200)
    destino = models.EmailField(max_length=200)
    cantidad = models.IntegerField()
    tipo = models.CharField(max_length=80, choices=tipos)
    observaciones = models.CharField(max_length=100)
    solicitado_por = models.CharField(max_length=200)
    aprobado_compra = models.CharField(max_length=200)
    foto_producto = models.ImageField(
        upload_to="fotos_empleados/", null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True)

    def es_extension_valida(self):
        extensiones_validas = [".jpg", ".jpeg", ".png", ".gif"]
        return any(
            self.foto_producto.name.lower().endswith(ext) for ext in extensiones_validas
        )

    """ la clase Meta dentro de un modelo se utiliza para proporcionar metadatos adicionales sobre el modelo."""

    class Meta:
        db_table = "empleados"
        ordering = ["-created_at"]
