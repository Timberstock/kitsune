# from xml.etree import ElementTree as ET
import lxml.etree as ET

from google.cloud import storage  # type: ignore


def upload_to_bucket(file_to_upload, file_name, bucket_name):
    """Upload the XML file to the bucket and return the public URL."""

    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(file_name)
    blob.upload_from_string(file_to_upload, content_type="application/xml")
    blob.make_public()
    return blob.public_url


def certificate_file(empresa_id: str):
    """Open the .pfx file and return it in requests format"""

    certificate_name = "CERTIF" + empresa_id + ".pfx"
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


def get_xml_file(rut_empresa, file_type, folio_or_CAF_count):
    """Open the CAF .xml file and return it in requests format"""

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


def string_to_xml(
    xml_string,
    rut_empresa,
    count,
    document_type,
    firebase_bucket_name,  # parameter just for now
):
    """Convert the XML string into a XML object and upload it to the bucket"""
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
    url = upload_to_bucket(string, filename, firebase_bucket_name)
    return url
