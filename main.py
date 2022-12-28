import requests
from args import ObtainFolios, GuiaDespachoDocumento, SobreCaratula, InfoEnvio
import firebase_admin
from firebase_admin import credentials
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from fastapi.exceptions import RequestValidationError
from functions import (
    auth_to_base64,
    certificate_file,
    decrypt_password,
    rut_empresa_to_str,
    string_to_xml,
    clean_null_terms,
    document_to_dict,
    get_xml_file,
)

firebase_admin.initialize_app()

app = FastAPI()
AUTH = auth_to_base64()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return PlainTextResponse(str(exc), status_code=400)


@app.get("/")
def root():
    return {"message": "Hello World"}


# GET 127.0.0.1:8000/folios/770685532 body: {"amount": 5}
@app.post("/folios/{rut_empresa}")
def obtain_new_folios(
    rut_empresa: int,
    obtain_folios_args: ObtainFolios,
):
    folios_amount = obtain_folios_args.amount
    try:
        url = f"https://servicios.simpleapi.cl/api/folios/get/52/{folios_amount}"
        # El body hay que leerlo de la base de datos, hay que recibir
        # solo el rut de la empresa del path param y con eso
        # obtener el password y el rut del certificado
        body = {
            "RutCertificado": "16018824-3",
            "Password": decrypt_password(
                "gAAAAABjlzT__sYwYInohIOVb6_QAfBm-XfB18brXKsLyfEpbd1uB4T0gGCLRoMxj-enRiOZFvrak1ezEAUpNu_nN8IOsNpwrQ==".encode()
            ),
            "RutEmpresa": rut_empresa_to_str(rut_empresa),
            "Ambiente": 0,
        }
        # Hay que leer el caf_count desde la base de datos también para saber cual corresponde
        caf_count = 1
        payload = {"input": str(dict(body))}
        files = [certificate_file(rut_empresa)]
        headers = {"Authorization": AUTH}
        response = requests.post(url, headers=headers, data=payload, files=files)
        # if response.status_code == 200:
        #     string_to_xml(response.text, rut_empresa, caf_count, "CAF")
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
@app.get("/folios/{rut_empresa}")
def available_folios(rut_empresa: str):
    try:
        url = "https://servicios.simpleapi.cl/api/folios/get/33/"
        # El body hay que leerlo de la base de datos, hay que recibir
        # solo el rut de la empresa del path param y con eso
        # obtener el password y el rut del certificado
        body = {
            "RutCertificado": "16018824-3",
            "Password": decrypt_password(
                "gAAAAABjlzT__sYwYInohIOVb6_QAfBm-XfB18brXKsLyfEpbd1uB4T0gGCLRoMxj-enRiOZFvrak1ezEAUpNu_nN8IOsNpwrQ==".encode()
            ),
            "RutEmpresa": rut_empresa_to_str(rut_empresa),
            "Ambiente": 0,
        }
        payload = {"input": str(dict(body))}
        files = [certificate_file(rut_empresa)]
        headers = {"Authorization": AUTH}
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
# GET 127.0.0.1:8000//dte/770685532/guia-despacho
@app.post("/dte/{rut_empresa}")
def generate_dte_guiadespacho(rut_empresa: int, document: GuiaDespachoDocumento):
    try:
        document = document_to_dict(document)
        document = clean_null_terms(document)
        # Esto hay que hacerlo buscando en la base de datos con el rut_empresa dado
        certificate = {
            "RutCertificado": "16018824-3",
            "Password": decrypt_password(
                "gAAAAABjlzT__sYwYInohIOVb6_QAfBm-XfB18brXKsLyfEpbd1uB4T0gGCLRoMxj-enRiOZFvrak1ezEAUpNu_nN8IOsNpwrQ==".encode()
            ),
        }
        url = "https://api.simpleapi.cl/api/v1/dte/generar"
        payload = {"input": str({"Documento": document, "Certificado": certificate})}
        NumFolio = document["Encabezado"]["IdentificacionDTE"]["Folio"]
        caf_count = 1
        files = [
            certificate_file(rut_empresa),
            get_xml_file(rut_empresa, "CAF", caf_count),
        ]
        headers = {"Authorization": AUTH}
        response = requests.post(url, headers=headers, data=payload, files=files)
        if response.status_code == 200:
            # ACA YA PODRIAMOS CREAR EL OBJETO DTE Y GUARDARLO EN FIRESTORE
            # CON UN FLAG DE QUE AUN NO HA SIDO ENVIADO
            url = string_to_xml(response.text, rut_empresa, NumFolio, "GD")
            return {
                "status_code": response.status_code,
                "message": "DTE generado correctamente",
                "url": url,
            }
        else:
            return {
                "status_code": response.status_code,
                "message": response.reason,
            }

    except requests.exceptions.RequestException as e:
        return {
            "message": str(e),
        }
        raise SystemExit(e)
    except Exception as e:
        return {
            "message": str(e),
        }
        # raise SystemExit(e)


# Se genera un sobre de envio DTE a partir de los numeros de folio que
# aun no han sido enviados
@app.post("/sobre/{rut_empresa}")
def generate_sobre(rut_empresa: int, caratula_info: SobreCaratula):
    try:
        # Esto hay que hacerlo buscando en la base de datos con el rut_empresa dado
        certificate = {
            "Rut": "16018824-3",
            "Password": decrypt_password(
                "gAAAAABjlzT__sYwYInohIOVb6_QAfBm-XfB18brXKsLyfEpbd1uB4T0gGCLRoMxj-enRiOZFvrak1ezEAUpNu_nN8IOsNpwrQ==".encode()
            ),
        }
        caratula = dict(caratula_info)
        if caratula["RutEmisor"] == None:
            caratula["RutEmisor"] = rut_empresa_to_str(rut_empresa)
        payload = {"input": str({"Certificado": certificate, "Caratula": caratula})}
        url = "https://api.simpleapi.cl/api/v1/envio/generar"
        # Esto también hay que hacerlo buscando en la base de datos con el rut_empresa
        # viendo los numeros de folios que quedan disponibles sin ocupar de los solicitados
        sobre_count_siguiente = 4
        folios_sin_enviar = [6]
        files = [certificate_file(rut_empresa)]
        for folio in folios_sin_enviar:
            files.append(get_xml_file(rut_empresa, "GD", folio))
        headers = {"Authorization": AUTH}
        response = requests.post(url, headers=headers, data=payload, files=files)
        # Este numero hay que obtenerlo de base de datos tambien
        # if response.status_code == 200:
        #     # ACA YA PODRIAMOS CREAR EL OBJETO DTE Y GUARDARLO EN FIRESTORE
        #     # CON UN FLAG DE QUE AUN NO HA SIDO ENVIADO
        #     string_to_xml(
        #         response.text,
        #         rut_empresa,
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
@app.post("/sobre/{rut_empresa}/enviar")
def enviar_sobre(rut_empresa: int, info_envio: InfoEnvio):
    try:
        # SACARLO DE LA BASE DE DATOS CON EL rut_empresa
        certificate = {
            "Rut": "16018824-3",
            "Password": decrypt_password(
                "gAAAAABjlzT__sYwYInohIOVb6_QAfBm-XfB18brXKsLyfEpbd1uB4T0gGCLRoMxj-enRiOZFvrak1ezEAUpNu_nN8IOsNpwrQ==".encode()
            ),
        }
        info_envio = dict(info_envio)
        info_envio["Certificado"] = certificate
        payload = {"input": str(info_envio)}
        url = "https://api.simpleapi.cl/api/v1/envio/enviar"
        # ACA HAY QUE VER EN LA BASE DE DATOS QUE SOBRE CORRESPONDE ENVIAR
        sobre_a_enviar = 4
        files = [
            certificate_file(rut_empresa),
            get_xml_file(rut_empresa, "SOBRE", sobre_a_enviar),
        ]
        headers = {"Authorization": AUTH}
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
@app.get("/sobre/{rut_empresa}/{track_id}")
def get_sobre_status(rut_empresa: int, track_id: int):
    try:
        # SACARLO DE LA BASE DE DATOS CON EL rut_empresa
        certificate = {
            "Rut": "16018824-3",
            "Password": decrypt_password(
                "gAAAAABjlzT__sYwYInohIOVb6_QAfBm-XfB18brXKsLyfEpbd1uB4T0gGCLRoMxj-enRiOZFvrak1ezEAUpNu_nN8IOsNpwrQ==".encode()
            ),
        }
        body = {
            "RutEmpresa": rut_empresa_to_str(rut_empresa),
            # TrackID probablemente leerlos de una cola
            "TrackId": track_id,
            "Ambiente": 0,
            "ServidorBoletaREST": "false",
        }
        body["Certificado"] = certificate
        payload = {"input": str(body)}
        files = [
            certificate_file(rut_empresa),
        ]
        headers = {"Authorization": AUTH}
        url = "https://api.simpleapi.cl/api/v1/consulta/envio"
        response = requests.post(url, headers=headers, data=payload, files=files)
        if response.status_code == 200:
            # ACA HAY QUE HACER EL CAMBIO DE ESTADO EN LA BASE DE DATOS PARA SABER
            # SI SE RECHAZÓ O SE ACEPTÓ
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
