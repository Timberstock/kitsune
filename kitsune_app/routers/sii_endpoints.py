# change requests if async http calls are needed for more concurrent requests
import requests  # type: ignore
import datetime

from fastapi import APIRouter, Depends

from kitsune_app.dependencies.sii import empresa_context, document_to_guia
from kitsune_app.schemas import EmpresaContext
from kitsune_app.schemas.dte import (
    GuiaDespachoDocumentoIn,
    InfoEnvioIn,
    ObtainFoliosIn,
    GenerateSobreIn,
    Caratula
)
from kitsune_app.settings import AUTH, FIREBASE_BUCKET
from kitsune_app.utils import (
    certificate_file,
    empresa_id_to_rut_empresa,
    get_xml_file_tuple_for_request,
    upload_xml_string_to_bucket,
)

import json


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
    document: GuiaDespachoDocumentoIn,
    guia_despacho: dict = Depends(document_to_guia),
    context: EmpresaContext = Depends(empresa_context),
):
    """
    Main endpoint of the API, generates a DTE Guia de Despacho with
    GuiaDespachoDocumento in the body of the request and returns an url for the DTE in
    a .xml file if succeeds.
    """
    try:
        empresa_id = context.empresa_id
        certificate = context.pfx_certificate
        url = "https://api.simpleapi.cl/api/v1/dte/generar"
        payload = {
            "input": str({"Documento": guia_despacho, "Certificado": certificate})
        }
        folio = int(guia_despacho["Encabezado"]["IdentificacionDTE"]["Folio"])
        files = [
            certificate_file(empresa_id),
            get_xml_file_tuple_for_request(empresa_id, "CAF", FIREBASE_BUCKET, folio_or_sobre_count=folio),
        ]
        headers = {"Authorization": AUTH}
        # TODO: use httpx instead of requests
        response = requests.post(url, headers=headers, data=payload, files=files)
        # print(response.status_code)
        # print(response.reason)
        # print(response.text)
        if response.status_code == 200:
            guia_xml = response.text
            url = upload_xml_string_to_bucket(
                empresa_id, guia_xml, "GD", FIREBASE_BUCKET, folio
            )
            print(url)
            # return JSONResponse(status_code=status.HTTP_201_CREATED,
            #                     content=response_dict)
            return {
                "status_code": response.status_code,
                "message": "DTE generado correctamente",
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
        return {
            "message": str(e),
        }

    except Exception as e:
        print(e)
        return {
            "message": str(e),
        }


@router.post("/sobre/{empresa_id}")
def generate_sobre(
    generate_sobre_params: GenerateSobreIn, context: EmpresaContext = Depends(empresa_context)
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
        # TODO: sobres are going to be generated daily, so we need to get the last sobre
        # count from the bucket
        # sobre_count_siguiente = 4
        folios_sin_enviar = generate_sobre_params.folios
        files = [certificate_file(empresa_id)]
        for folio in folios_sin_enviar:
            files.append(get_xml_file_tuple_for_request(empresa_id, "GD", FIREBASE_BUCKET, folio_or_sobre_count= folio))
        print(f"payload: {payload}")
        print(f"files: {files}")
        headers = {"Authorization": AUTH}
        # TODO: use httpx instead of requests
        response = requests.post(url, headers=headers, data=payload, files=files)
        print(response.status_code)
        print(response.reason)
        print(response.text)
        if response.status_code == 200:
            today = datetime.date.today()
            url = upload_xml_string_to_bucket(
                empresa_id,
                response.text,
                "SOBRE",
                FIREBASE_BUCKET,
                date=today,
            )
            return {
                "status_code": response.status_code,
                "reason": response.reason,
                "url": url,
                "date": today,
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
# este endpoint a veces tiene problemas en el request a SimpleAPI, por lo que
# cuando se trata de problemas de servidor, token, etc hay que settearlo
# para que se vuelva a intentar hasta que funcione o envie un error de schema
@router.post("/sobre/{empresa_id}/enviar")
def enviar_sobre(
    info_envio_body: InfoEnvioIn, context: EmpresaContext = Depends(empresa_context)
):
    try:
        # It will only be one in the meantime, but they can be several
        sobre_date = info_envio_body.sobres_dates[0]
        empresa_id = context.empresa_id
        certificate = context.pfx_certificate
        info_envio = dict(info_envio_body)
        info_envio["Certificado"] = certificate
        payload = {"input": str(info_envio)}
        url = "https://api.simpleapi.cl/api/v1/envio/enviar"
        files = [
            certificate_file(empresa_id),
            get_xml_file_tuple_for_request(empresa_id, "SOBRE", FIREBASE_BUCKET, date=sobre_date),
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
