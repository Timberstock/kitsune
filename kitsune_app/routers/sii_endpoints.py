# change requests if async http calls are needed for more concurrent requests
import datetime
import json

import requests  # type: ignore

from fastapi import APIRouter, Depends

from kitsune_app.dependencies.sii import document_to_guia, empresa_context
from kitsune_app.schemas import EmpresaContext
from kitsune_app.schemas.dte import (
    ConsultarEstadoDTEIn,
    GenerateGuiaDespachoIn,
    GenerateSobreIn,
    InfoEnvioIn,
    ObtainFoliosIn,
)
from kitsune_app.settings import AUTH, FIREBASE_BUCKET
from kitsune_app.utils import (
    certificate_file,
    create_and_upload_pdf_from_html_string,
    empresa_id_to_rut_empresa,
    get_logo_base64,
    get_xml_file_tuple_for_request,
    upload_xml_string_to_bucket,
)


router = APIRouter(tags=["SII"])


# POST 127.0.0.1:8000/folios/770685532 body: {"amount": 5}
@router.post("/folios/{empresa_id}")
def obtain_new_folios(
    obtain_folios_args: ObtainFoliosIn,
    context: EmpresaContext = Depends(empresa_context),
):
    empresa_id = context.empresa_id
    certificate = context.pfx_certificate
    folios_amount = obtain_folios_args.amount
    try:
        url = f"https://servicios.simpleapi.cl/api/folios/get/52/{folios_amount}"
        body = {
            **certificate,
            "RutEmpresa": empresa_id_to_rut_empresa(empresa_id),
            "Ambiente": 0,
        }

        # TODO: should be retrieved according to the folio number instead
        # caf_count
        payload = {"input": str(dict(body))}
        files = [certificate_file(empresa_id)]
        headers = {"Authorization": AUTH}
        # TODO: use httpx instead of requests
        response = requests.post(url, headers=headers, data=payload, files=files)
        # if response.status_code == 200:
        #     upload_xml_string_to_bucket(response.text, empresa_id, caf_count, "CAF")
        return {
            "status_code": response.status_code,
            "reason": response.reason,
            "text": response.text,
        }
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)
    except Exception as e:
        raise SystemExit(e)


# GET 127.0.0.1:8000/folios/770685532
@router.get("/folios/{empresa_id}")
def available_folios(context: EmpresaContext = Depends(empresa_context)):
    try:
        empresa_id = context.empresa_id
        certificate = context.pfx_certificate
        url = "https://servicios.simpleapi.cl/api/folios/get/52/"
        body = {
            **certificate,
            "RutEmpresa": empresa_id_to_rut_empresa(empresa_id),
            "Ambiente": 0,
        }
        payload = {"input": str(dict(body))}
        files = [certificate_file(empresa_id)]
        headers = {"Authorization": AUTH}
        # TODO: use httpx instead of requests
        response = requests.post(url, headers=headers, data=payload, files=files)
        return {
            "status_code": response.status_code,
            "reason": response.reason,
            "text": response.text,
        }
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)
    except Exception as e:
        raise SystemExit(e)


# Genera un DTE Guia de Despacho en un archivo .xml
@router.post("/dte/{empresa_id}")
def generate_dte_guiadespacho(
    generate_dte_params: GenerateGuiaDespachoIn,
    guia_despacho: dict = Depends(document_to_guia),
    context: EmpresaContext = Depends(empresa_context),
):
    """
    Main endpoint of the API, generates a DTE Guia de Despacho with
    GuiaDespachoDocumento in the params of the request and returns an url for the DTE in
    a .xml file and another one for .pdf if succeeds (stored in Firestore)
    """
    try:
        empresa_id = context.empresa_id
        certificate = context.pfx_certificate
        url = "https://api.simpleapi.cl/api/v1/dte/generar"
        payload = {
            "input": str({"Documento": guia_despacho, "Certificado": certificate})
        }
        print(guia_despacho)
        folio = int(guia_despacho["Encabezado"]["IdentificacionDTE"]["Folio"])
        files = [
            certificate_file(empresa_id),
            get_xml_file_tuple_for_request(
                empresa_id, "CAF", FIREBASE_BUCKET, folio_or_sobre_count=folio
            ),
        ]
        headers = {"Authorization": AUTH}
        # Get the XML from SimpleAPI as string
        print("Generating XML file for Guia de Despacho...")
        response_xml = requests.post(url, headers=headers, data=payload, files=files)

        if response_xml.status_code == 200:
            guia_xml = response_xml.text
            # Upload the XML to Firebase Storage
            print("Uploading XML file to Firebase Storage...")
            xml_url = upload_xml_string_to_bucket(
                empresa_id, guia_xml, "GD", FIREBASE_BUCKET, folio
            )
            try:
                # Get the barcode from SimpleAPI
                pdf_html_string = generate_dte_params.pdf_html_string
                url = "https://api.simpleapi.cl/api/v1/impresion/timbre"
                print("Generating barcode...")
                gd_file = get_xml_file_tuple_for_request(
                    empresa_id, "GD", FIREBASE_BUCKET, folio_or_sobre_count=folio
                )
                files = [gd_file]
                response_barcode = requests.post(url, headers=headers, files=files)
                barcode_png_base64 = response_barcode.text
                # Embed the image in the HTML string
                pdf_html_string_with_barcode = pdf_html_string.replace(
                    "</body>",
                    '<div style="position: absolute; left: 187.5px">'
                    f'<img src="data:image/png;base64,{barcode_png_base64}"'
                    'style="width: 275px; height: 132px" />'
                    "</div>"
                    "</body>",
                )

                # Get logo from Firebase Storage in base64 and replace it in the HTML
                logo_base64 = get_logo_base64(empresa_id, FIREBASE_BUCKET)
                pdf_html_string_with_barcode = pdf_html_string_with_barcode.replace(
                    '<img src="placeholder.png" alt="logo" />',
                    f'<img src="data:image/png;base64,{logo_base64}"'
                    'alt="logo" style="height: 80px"/>',
                )

                # Generate the PDF from the HTML string
                print("Generating PDF file...")
                pdf_url = create_and_upload_pdf_from_html_string(
                    empresa_id, pdf_html_string_with_barcode, FIREBASE_BUCKET, folio
                )

                if response_barcode.status_code == 200:
                    print(
                        f'"[{response_barcode.status_code}] PDF'
                        f'URL for Guia Folio {folio}: {pdf_url}"'
                    )
                    return {
                        "status_code": response_barcode.status_code,
                        "message": "XML y PDF generado correctamente",
                        "xml_url": xml_url,
                        "pdf_url": pdf_url,
                    }
                else:
                    print(
                        f'"[{response_barcode.status_code}]'
                        f"{response_barcode.reason}:"
                        '{response_barcode.text}"'
                    )
                    return {
                        "status_code": response_barcode.status_code,
                        "message": f"[barcode]{response_barcode.reason}:"
                        f'{response_barcode.text}"',
                    }
            except Exception as e:
                print(e)
                return {
                    "status_code": 600,
                    "message": "[barcode] XML generado, error en creacion de PDF",
                    "url": xml_url,
                }
        else:
            print(
                f"{response_xml.status_code}:"
                f"{response_xml.reason}:"
                f"{response_xml.text}"
            )
            return {
                "status_code": response_xml.status_code,
                "message": f"{response_xml.reason}: {response_xml.text}",
            }

    except requests.exceptions.RequestException as e:
        print(e)
        return {
            "status_code": e.response.status_code,
            "message": str(e),
        }

    except Exception as e:
        print(e)
        return {
            "status_code": 601,
            "message": str(e),
        }


@router.post("/sobre/{empresa_id}")
def generate_sobre(
    generate_sobre_params: GenerateSobreIn,
    context: EmpresaContext = Depends(empresa_context),
):
    """
    Generates a Sobre DTE with the folios that have not been sent yet, stores it in
    the firebase bucket and returns its url.
    It handles the corresponding number of Sobre by looking at the firestore Sobres
    subcollection of the empresa_id.
    """
    try:
        empresa_id = context.empresa_id
        certificate = context.pfx_certificate
        # SEND FROM CLOUD FUNCTIONS THIS INFO
        caratula_info = generate_sobre_params.caratula.dict()
        caratula = dict(caratula_info)
        if caratula["RutEmisor"] is None:
            caratula["RutEmisor"] = empresa_id_to_rut_empresa(empresa_id)
        payload = {"input": str({"Certificado": certificate, "Caratula": caratula})}
        url = "https://api.simpleapi.cl/api/v1/envio/generar"
        folios_sin_enviar = generate_sobre_params.folios
        files = [certificate_file(empresa_id)]
        for folio in folios_sin_enviar:
            files.append(
                get_xml_file_tuple_for_request(
                    empresa_id, "GD", FIREBASE_BUCKET, folio_or_sobre_count=folio
                )
            )
        print(f"payload: {payload}")
        print(f"files: {files}")
        headers = {"Authorization": AUTH}
        # TODO: use httpx instead of requests
        response = requests.post(url, headers=headers, data=payload, files=files)
        print(response.status_code)
        print(response.reason)
        if response.status_code == 200:
            url = upload_xml_string_to_bucket(
                empresa_id,
                response.text,
                "SOBRE",
                FIREBASE_BUCKET,
                id=generate_sobre_params.sobre_id,
            )
            return {
                "status_code": response.status_code,
                "reason": response.reason,
                "url": url,
            }
        else:
            print(f"{response.status_code}: {response.reason}: {response.text}")
            return {
                "status_code": response.status_code,
                "message": f"{response.reason}: {response.text}",
            }

    except requests.exceptions.RequestException as e:
        print(e)
        raise SystemExit(e)
    except Exception as e:
        print(e)
        raise SystemExit(e)


# Se envian los sobres de envio de DTEs que no han sido enviados al SII.
# Este endpoint a veces tiene problemas en el request a SimpleAPI, por lo que
# cuando se trata de problemas de servidor, token, etc hay que settearlo
# para que se vuelva a intentar hasta que funcione o envie un error de schema
@router.post("/sobre/{empresa_id}/enviar")
def enviar_sobre(
    info_envio_body: InfoEnvioIn, context: EmpresaContext = Depends(empresa_context)
):
    try:
        # It will only be one in the meantime, but they can be several
        sobre_id = info_envio_body.sobres_document_ids[0]
        empresa_id = context.empresa_id
        certificate = context.pfx_certificate
        info_envio = dict(info_envio_body)
        info_envio["Certificado"] = certificate
        payload = {"input": str(info_envio)}
        url = "https://api.simpleapi.cl/api/v1/envio/enviar"
        files = [
            certificate_file(empresa_id),
            get_xml_file_tuple_for_request(
                empresa_id, "SOBRE", FIREBASE_BUCKET, id=sobre_id
            ),
        ]
        headers = {"Authorization": AUTH}
        # TODO: use httpx instead of requests
        response = requests.post(url, headers=headers, data=payload, files=files)
        # TODO: ERROR HERE
        print(response.status_code)
        print(response.reason)
        print(response.text)
        if response.status_code == 200:
            response_dict = json.loads(response.text)
            print(response_dict["trackId"])
            return {
                "status_code": response.status_code,
                "reason": response.reason,
                "text": response.text,
                "trackId": response_dict.get("trackId", "Send Failed"),
            }
        else:
            return {
                "status_code": response.status_code,
                "message": f"{response.reason}: {response.text}",
            }
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)
    except Exception as e:
        raise SystemExit(e)


# Se obtiene el estado del sobre de envío que fue enviado al SII
# y que aun no se sabe si fueron aceptados o rechazados (estado indeterminado
# o pendiente en la base de datos)
@router.get("/sobre/{empresa_id}/{track_id}")
def get_sobre_status(track_id: int, context: EmpresaContext = Depends(empresa_context)):
    try:
        empresa_id = context.empresa_id
        certificate = context.pfx_certificate
        body = {
            "RutEmpresa": empresa_id_to_rut_empresa(empresa_id),
            # probably read them from a queue
            "TrackId": track_id,
            "Ambiente": 0,
            "ServidorBoletaREST": "false",
        }
        body["Certificado"] = certificate
        payload = {"input": str(body)}
        files = [
            certificate_file(empresa_id),
        ]
        headers = {"Authorization": AUTH}
        url = "https://api.simpleapi.cl/api/v1/consulta/envio"
        response = requests.post(url, headers=headers, data=payload, files=files)
        if response.status_code == 200:
            # Parse string to json
            response_dict = json.loads(response.text)
            estados: list = response_dict.get("estados", [])
            print(response_dict)
            return {
                "status_code": response.status_code,
                "reason": response.reason,
                "estados": response_dict.get("estados", "Send Failed"),
                "text": response.text,
            }
        else:
            return {
                "status_code": response.status_code,
                "message": f"{response.reason}: {response.text}",
            }

    except requests.exceptions.RequestException as e:
        raise SystemExit(e)
    except Exception as e:
        raise SystemExit(e)


@router.get("/dte/{empresa_id}/{folio}/validar")
def get_validacion_dte(folio: int, context: EmpresaContext = Depends(empresa_context)):
    try:
        empresa_id = context.empresa_id
        payload = {"input": "{Tipo:1}"}
        files = [
            get_xml_file_tuple_for_request(
                empresa_id, "GD", FIREBASE_BUCKET, folio_or_sobre_count=folio
            ),
        ]
        headers = {"Authorization": AUTH}
        url = "https://api.simpleapi.cl/api/v1/consulta/validador"
        response = requests.post(url, headers=headers, data=payload, files=files)
        if response.status_code == 200:
            # TODO: save the result in the firestore document if succesful or failed
            print(response)
            print(response.text)
            pass
        return {
            "status_code": response.status_code,
            "reason": response.reason,
            "text": response.text,
        }

    except requests.exceptions.RequestException as e:
        raise SystemExit(e)
    except Exception as e:
        raise SystemExit(e)


@router.get("/dte/{empresa_id}/consultar-estado")
def consultar_estado_dte(
    params: ConsultarEstadoDTEIn, context: EmpresaContext = Depends(empresa_context)
):
    try:
        print(params)
        empresa_id = context.empresa_id
        certificate = context.pfx_certificate
        body = {
            "Certificado": certificate,
            "RutEmpresa": empresa_id_to_rut_empresa(empresa_id),
            "RutReceptor": params.rut_receptor,
            "Folio": params.folio,
            "Total": params.monto,
            "FechaDTE": params.fecha_dte,
            "Tipo": params.tipo_dte,
            "Ambiente": params.ambiente,
            "ServidorBoletaREST": "false",
        }
        payload = {"input": str(body)}
        files = [
            certificate_file(empresa_id),
        ]
        headers = {"Authorization": AUTH}
        url = "https://api.simpleapi.cl/api/v1/consulta/dte"
        response = requests.post(url, headers=headers, data=payload, files=files)
        if response.status_code == 200:
            # TODO: save the result in the firestore document if succesful or failed
            print(response)
            print(response.text)
            pass
        return {
            "status_code": response.status_code,
            "reason": response.reason,
            "text": response.text,
        }

    except requests.exceptions.RequestException as e:
        raise SystemExit(e)
    except Exception as e:
        raise SystemExit(e)
