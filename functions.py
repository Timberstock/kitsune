import base64
import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from google.cloud import storage

# from xml.etree import ElementTree as ET
import lxml.etree as ET
from pydantic import BaseModel

load_dotenv()


def upload_to_bucket(
    file_to_upload, file_name, bucket_name=os.getenv("FIREBASE_BUCKET")
):
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(file_name)
    blob.upload_from_string(file_to_upload, content_type="application/xml")
    blob.make_public()
    print(blob.public_url)
    return blob.public_url


# This function is used to decrypt the password from PostgreSQL db
def decrypt_password(encrypted_password):
    password_key = b"pass"
    salt = os.getenv("SALT").encode()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=39000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password_key))
    f = Fernet(key)
    return f.decrypt(encrypted_password).decode()


# This function is used to convert the API key into a base64 string
def auth_to_base64():
    SimpleAPI_KEY = os.getenv("SIMPLEAPI_KEY")
    SimpleAPI_KEY = ("api:" + SimpleAPI_KEY).encode("ascii")
    SimpleAPI_KEY = base64.b64encode(SimpleAPI_KEY)
    base64_message = SimpleAPI_KEY.decode("ascii")
    auth_64_message = "Basic " + base64_message
    return auth_64_message


# This function is used to open the .pfx file and return it in requests format
def certificate_file(rut_empresa):
    rut_empresa = str(rut_empresa)
    certificate_name = "CERTIF" + rut_empresa[:-1] + ".pfx"
    cert_file = (
        "file",
        (
            certificate_name,
            open(
                "files/" + certificate_name,
                "rb",
            ),
            "application/octet-stream",
        ),
    )
    return cert_file


# This function is used to open the CAF .xml file and return it in requests format
def get_xml_file(rut_empresa, file_type, folio_or_CAF_count):
    rut_empresa = str(rut_empresa)
    if file_type == "CAF":
        file_name = "CAF" + rut_empresa[:-1] + "n" + str(folio_or_CAF_count) + ".xml"
    elif file_type == "GD":
        file_name = (
            "DTE_GD_" + rut_empresa[:-1] + "f" + str(folio_or_CAF_count) + ".xml"
        )
    elif file_type == "SOBRE":
        file_name = "SOBRE_" + rut_empresa[:-1] + "n" + str(folio_or_CAF_count) + ".xml"
    file_file = (
        "file",
        (
            file_name,
            open(
                "files/" + file_name,
                "rb",
            ),
            "text/xml",
        ),
    )
    return file_file


# This function is used to convert the XML string into a XML object
def string_to_xml(xml_string, rut_empresa, count, document_type):
    rut_empresa = str(rut_empresa)
    # tree = ET.XML(xml_string)
    tree = ET.fromstring(bytes(xml_string, encoding="latin1"))
    if document_type == "CAF":
        filename = "CAF" + rut_empresa[:-1] + "n" + str(count) + ".xml"
    elif document_type == "GD":
        filename = "DTE_GD_" + rut_empresa[:-1] + "f" + str(count) + ".xml"
    elif document_type == "SOBRE":
        filename = "SOBRE_" + rut_empresa[:-1] + "n" + str(count) + ".xml"

    string = ET.tostring(tree, encoding="latin1")
    url = upload_to_bucket(
        string,
        filename,
    )
    return url


# This function is used to convert the PathParam rut_empresa into a string
def rut_empresa_to_str(rut_empresa):
    rut_empresa = str(rut_empresa)
    rut_empresa = rut_empresa[:-1] + "-" + rut_empresa[-1]
    return rut_empresa


# These functions are used to convert the pydantic models into a dictionary
# and clean null terms
def document_to_dict(document):
    document = dict(document)
    for key, value in document.items():
        if isinstance(value, BaseModel):
            document[key] = document_to_dict(value)
    return document


def clean_null_terms(d):
    clean = {}
    for k, v in d.items():
        if isinstance(v, dict):
            nested = clean_null_terms(v)
            if len(nested.keys()) > 0:
                clean[k] = nested
        elif v is not None:
            clean[k] = v
    return clean
