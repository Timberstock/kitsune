# change requests if async http calls are needed for more concurrent requests
import requests  # type: ignore

from fastapi import APIRouter, Depends

from kitsune_app.settings import AUTH, FIREBASE_BUCKET
from kitsune_app.utils import (
    certificate_file,
    clean_null_terms,
    document_to_dict,
    get_xml_file,
    empresa_id_to_rut_empresa,
    string_to_xml,
)

from kitsune_app.schemas.dte import GuiaDespachoDocumento, InfoEnvio, ObtainFoliosIn, SobreCaratula
from kitsune_app.dependencies.context import empresa_context
from kitsune_app.schemas import EmpresaContext


router = APIRouter(tags=["SII"])


# POST 127.0.0.1:8000/folios/770685532 body: {"amount": 5}
@router.post("/folios/{empresa_id}")
def obtain_new_folios(
    obtain_folios_args: ObtainFoliosIn,
    context: EmpresaContext = Depends(empresa_context)
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
        #     string_to_xml(response.text, empresa_id, caf_count, "CAF")
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
def available_folios(
    context: EmpresaContext = Depends(empresa_context)
):
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
def generate_dte_guiadespacho(document: GuiaDespachoDocumento, context: EmpresaContext = Depends(empresa_context)):
    try:
        guia_despacho = document_to_dict(document)
        guia_despacho = clean_null_terms(guia_despacho)
        empresa_id = context.empresa_id
        certificate = context.pfx_certificate
        url = "https://api.simpleapi.cl/api/v1/dte/generar"
        payload = {
            "input": str({"Documento": guia_despacho, "Certificado": certificate})
        }
        NumFolio = guia_despacho["Encabezado"]["IdentificacionDTE"]["Folio"]
        caf_count = 1
        files = [
            certificate_file(empresa_id),
            get_xml_file(empresa_id, "CAF", caf_count),
        ]
        headers = {"Authorization": AUTH}
        # TODO: use httpx instead of requests
        response = requests.post(url, headers=headers, data=payload, files=files)
        if response.status_code == 200:
            url = string_to_xml(
                response.text, empresa_id, NumFolio, "GD", FIREBASE_BUCKET
            )
            return {
                "status_code": response.status_code,
                "message": "DTE generado correctamente",
                "url": url,
            }
        else:
            return {
                "status_code": response.status_code,
                "message": f"{response.reason}: {response.text}",
            }

    except requests.exceptions.RequestException as e:
        return {
            "message": str(e),
        }
    except Exception as e:
        return {
            "message": str(e),
        }


# Se genera un sobre de envio DTE a partir de los numeros de folio que
# aun no han sido enviados
@router.post("/sobre/{empresa_id}")
def generate_sobre(caratula_info: SobreCaratula, context: EmpresaContext = Depends(empresa_context)):
    try:
        empresa_id = context.empresa_id
        certificate = context.pfx_certificate
        caratula = dict(caratula_info)
        if caratula["RutEmisor"] is None:
            caratula["RutEmisor"] = empresa_id_to_rut_empresa(empresa_id)
        payload = {"input": str({"Certificado": certificate, "Caratula": caratula})}
        url = "https://api.simpleapi.cl/api/v1/envio/generar"
        # TODO: sobres are going to be generated daily, so we need to get the last sobre
        # count from the bucket
        # sobre_count_siguiente = 4
        folios_sin_enviar = [6]
        files = [certificate_file(empresa_id)]
        for folio in folios_sin_enviar:
            files.append(get_xml_file(empresa_id, "GD", folio))
        headers = {"Authorization": AUTH}
        # TODO: use httpx instead of requests
        response = requests.post(url, headers=headers, data=payload, files=files)
        # Este numero hay que obtenerlo de base de datos tambien
        # if response.status_code == 200:
        #     # ACA YA PODRIAMOS CREAR EL OBJETO DTE Y GUARDARLO EN FIRESTORE
        #     # CON UN FLAG DE QUE AUN NO HA SIDO ENVIADO
        #     string_to_xml(
        #         response.text,
        #         empresa_id,
        #         sobre_count_siguiente,
        #         "SOBRE",
        #     )
        return {
            "status_code": response.status_code,
            "reason": response.reason,
            "text": response.text,
        }
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)
    except Exception as e:
        raise SystemExit(e)


# Se envian los sobres de envio de DTEs que no han sido enviados al SII.
# este endpoint a veces tiene problemas en el request a SimpleAPI, por lo que
# cuando se trata de problemas de servidor, token, etc hay que settearlo
# para que se vuelva a intentar hasta que funcione o envie un error de schema
@router.post("/sobre/{empresa_id}/enviar")
def enviar_sobre(info_envio_body: InfoEnvio, context: EmpresaContext = Depends(empresa_context)):
    try:
        empresa_id = context.empresa_id
        certificate = context.pfx_certificate
        info_envio = dict(info_envio_body)
        info_envio["Certificado"] = certificate
        payload = {"input": str(info_envio)}
        url = "https://api.simpleapi.cl/api/v1/envio/enviar"
        # TODO: sobres are going to be generated daily, so we need to get the last sobre
        # count from the bucket
        sobre_a_enviar = 4
        files = [
            certificate_file(empresa_id),
            get_xml_file(empresa_id, "SOBRE", sobre_a_enviar),
        ]
        headers = {"Authorization": AUTH}
        # TODO: use httpx instead of requests
        response = requests.post(url, headers=headers, data=payload, files=files)
        if response.status_code == 200:
            # ACA HAY QUE GUARDAR EL TrackID EN ALGUNA PARTE
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
        # TODO: use httpx instead of requests
        response = requests.post(url, headers=headers, data=payload, files=files)
        if response.status_code == 200:
            # TODO: save the result in the firestore document if succesful or failed
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
