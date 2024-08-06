from django.shortcuts import render, redirect
import os
import uuid
from django.core.files.uploadedfile import SimpleUploadedFile

from django.contrib import messages  # Para usar mensajes flash
from django.core.exceptions import ObjectDoesNotExist

# Para el informe (Reporte)
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph

import json

import logging

from django.http import HttpResponse, JsonResponse

from django.shortcuts import get_object_or_404
from .models import Empleado  # Importando el modelo de Empleado
from django.core.paginator import Paginator


def inicio(request):
    opciones_cantidad = [(str(cantidad), str(cantidad)) for cantidad in range(1, 1000)]
    data = {
        "opciones_cantidad": opciones_cantidad,
    }
    return render(request, "empleado/form_empleado.html", data)


def listar_empleados(request):
    empleados = Empleado.objects.all()

    # Configurar la paginación
    paginator = Paginator(empleados, 4)  # Por ejemplo, 10 empleados por página
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    data = {
        "empleados": page_obj,
    }
    return render(request, "empleado/lista_empleados.html", data)


def view_form_carga_masiva(request):
    return render(request, "empleado/form_carga_masiva.html")


def detalles_empleado(request, id):
    try:
        empleado = Empleado.objects.get(id=id)
        data = {"empleado": empleado}
        return render(request, "empleado/detalles.html", data)
    except Empleado.DoesNotExist:
        error_message = f"no existe ningún registro para la busqueda id: {id}"
        return render(
            request, "empleado/lista_empleados.html", {"error_message": error_message}
        )


def registrar_empleado(request):
    if request.method == "POST":
        """
        Iterando a través de todos los elementos en el diccionario request.POST,
        que contiene los datos enviados a través del método POST, e imprime cada par clave-valor en la consola
        for key, value in request.POST.items():
            print(f'{key}: {value}')
        """
        producto_servicio = request.POST.get("producto_servicio")
        descripcion = request.POST.get("descripcion")
        destino = request.POST.get("destino")
        cantidad = request.POST.get("cantidad")
        tipo = request.POST.get("tipo")
        observaciones = request.POST.get("observaciones")
        solicitado = request.POST.get("solicitado_por")
        aprobado = request.POST.get("aprobado_compra")

        # Obtén la imagen del formulario
        foto_producto = request.FILES.get("foto_producto")

        if foto_producto:
            foto_producto = generate_unique_filename(foto_producto)

        # Procesa los datos y guarda en la base de datos
        empleado = Empleado(
            producto_servicio=producto_servicio,
            descripcion=descripcion,
            destino=destino,
            cantidad=cantidad,
            tipo=tipo,
            observaciones=observaciones,
            solicitado_por=solicitado,
            aprobado_compra=aprobado,
            foto_producto=foto_producto,
        )
        empleado.save()

        messages.success(
            request,
            f"Felicitaciones, La Solicitud {producto_servicio} fue registrada correctamente 😉",
        )
        return redirect("listar_empleados")

    # Si no se ha enviado el formulario, simplemente renderiza la plantilla con el formulario vacío
    return redirect("inicio")


def view_form_update_empleado(request, id):
    try:
        empleado = Empleado.objects.get(id=id)
        opciones_cantidad = [
            (int(cantidad), int(cantidad)) for cantidad in range(1, 1000)
        ]

        data = {
            "empleado": empleado,
            "opciones_cantidad": opciones_cantidad,
        }
        return render(request, "empleado/form_update_empleado.html", data)
    except ObjectDoesNotExist:
        error_message = f"El Empleado con id: {id} no existe."
        return render(
            request, "empleado/lista_empleados.html", {"error_message": error_message}
        )


def actualizar_empleado(request, id):
    try:
        if request.method == "POST":
            # Obtén el empleado existente
            empleado = Empleado.objects.get(id=id)

            empleado.producto_servicio = request.POST.get("producto_servicio")
            empleado.descripcion = request.POST.get("descripcion")
            empleado.destino = request.POST.get("destino")
            empleado.cantidad = int(request.POST.get("cantidad"))
            empleado.tipo = request.POST.get("tipo")
            empleado.solicitado_por = request.POST.get("solicitado_por")
            empleado.aprobado_compra = request.POST.get("aprobado_compra")

            # Convierte el valor a Decimal
            observaciones = request.POST.get("observaciones")
            empleado.observaciones = observaciones

            if "foto_producto" in request.FILES:
                # Actualiza la imagen solo si se proporciona en la solicitud
                empleado.foto_producto = generate_unique_filename(
                    request.FILES["foto_producto"]
                )

            empleado.save()
        return redirect("listar_empleados")
    except ObjectDoesNotExist:
        error_message = f"El Empleado con id: {id} no se actualizó."
        return render(
            request, "empleado/lista_empleados.html", {"error_message": error_message}
        )


def informe_empleado(request):
    try:
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="informe_empleado.pdf"'

        # Crear un objeto PDF
        doc = SimpleDocTemplate(response, pagesize=letter)
        styles = getSampleStyleSheet()
        style_heading = styles["Heading1"]
        style_body = styles["BodyText"]

        # Datos de empleados desde la base de datos
        datos = Empleado.objects.all()

        if not datos.exists():
            return HttpResponse(
                "No hay datos de empleados disponibles para generar el informe."
            )

        # Contenido del PDF (Tabla de empleados)
        contenido = []
        encabezados = (
            "producto_servicio",
            "descripcion",
            "destino",
            "cantidad",
            "tipo",
            "Observaciones",
            "Solicitado",
            "Aprobado",
            "Fecha",
        )
        contenido.append(encabezados)

        for empleado in datos:
            contenido.append(
                (
                    empleado.producto_servicio,
                    empleado.descripcion,
                    empleado.destino,
                    empleado.cantidad,
                    empleado.tipo,
                    empleado.observaciones,
                    empleado.solicitado_por,
                    empleado.aprobado_compra,
                    empleado.created_at.strftime(
                        "%Y-%m-%d"
                    ),  # Convertir la fecha a una cadena
                )
            )

        # Crear la tabla para el contenido
        tabla = Table(contenido)
        tabla.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("COLWIDTHS", (0, 0), (-1, -1), 72),  # Adjust column widths
                ]
            )
        )

        # Generar el contenido del PDF
        contenido_pdf = []
        contenido_pdf.append(Paragraph("Informe de Solicitudes", style_heading))
        contenido_pdf.append(
            Paragraph(
                "Este es un informe generado automáticamente con los datos de Solicitudes.",
                style_body,
            )
        )
        contenido_pdf.append(tabla)

        # Construir el PDF
        doc.build(contenido_pdf)

        return response

    except Exception as e:
        logging.error(f"Error al generar el informe PDF: {str(e)}")
        return HttpResponse(f"Error al generar el informe PDF: {str(e)}")


def eliminar_empleado(request):
    if request.method == "POST":
        id_empleado = json.loads(request.body)["idEmpleado"]
        # Busca el empleado por su ID
        empleado = get_object_or_404(Empleado, id=id_empleado)
        # Realiza la eliminación del empleado
        empleado.delete()
        return JsonResponse({"resultado": 1})
    return JsonResponse({"resultado": 1})


def cargar_archivo(request):
    try:
        if request.method == "POST":
            archivo_xlsx = request.FILES["archivo_xlsx"]
            if archivo_xlsx.name.endswith(".xlsx"):
                df = pd.read_excel(archivo_xlsx, header=3)

                for _, row in df.iterrows():
                    producto_servicio = row["Nombre"]
                    descripcion = row["Descripcion"]
                    cantidad = row["Cantidad"]
                    destino = row["Destino"]
                    tipo = row["Tipo"]
                    observaciones = row["Observaciones"]
                    solicitado_por = row["Solicitado"]
                    aprobado_compra = row["Aprobado"]

                    empleado, creado = Empleado.objects.update_or_create(
                        destino=destino,
                        defaults={
                            "producto_servicio": producto_servicio,
                            "descripcion": descripcion,
                            "cantidad": cantidad,
                            "destino": destino,
                            "tipo": tipo,
                            "observaciones": observaciones,
                            "solicitado_por": solicitado_por,
                            "aprobado_compra": aprobado_compra,
                            "foto_producto": "",
                        },
                    )

                return JsonResponse(
                    {
                        "status_server": "success",
                        "message": "Los datos se importaron correctamente.",
                    }
                )
            else:
                return JsonResponse(
                    {
                        "status_server": "error",
                        "message": "El archivo debe ser un archivo de Excel válido.",
                    }
                )
        else:
            return JsonResponse(
                {"status_server": "error", "message": "Método HTTP no válido."}
            )

    except Exception as e:
        logging.error("Error al cargar el archivo: %s", str(e))
        return JsonResponse(
            {
                "status_server": "error",
                "message": f"Error al cargar el archivo: {str(e)}",
            }
        )


# Genera un nombre único para el archivo utilizando UUID y conserva la extensión.
def generate_unique_filename(file):
    extension = os.path.splitext(file.name)[1]
    unique_name = f"{uuid.uuid4()}{extension}"
    return SimpleUploadedFile(unique_name, file.read())
