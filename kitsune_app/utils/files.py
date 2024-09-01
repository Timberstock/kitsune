# from xml.etree import ElementTree as ET
import base64

from typing import Optional

import lxml.etree as ET

from google.cloud import storage  # type: ignore
from weasyprint import HTML  # type: ignore


def get_xml_file_tuple_for_request(
    empresa_id, file_type, bucket_name, folio_or_sobre_count=0, CAF_step=50, id=""
):
    """Open the .xml file from cloud storage and return it in buffer.
    Keep in mind that the CAF_step must be sync with the ObtainFoliosIn.amount in dte.py
    """
    if file_type == "CAF":
        CAF_number = (folio_or_sobre_count - 1) // CAF_step
        file_name = f"CAF{empresa_id}n{CAF_number}.xml"
    elif file_type == "GD":
        file_name = f"DTE_GD_{empresa_id}f{folio_or_sobre_count}.xml"
    elif file_type == "SOBRE":
        file_name = f"SOBRE_{id}.xml"
    bucket_file = _read_from_bucket(file_name, bucket_name)

    file_file = (
        "file",
        (
            file_name,
            bucket_file,
            "text/xml",
        ),
    )
    return file_file


def get_logo_base64(empresa_id: str, bucket_name: Optional[str]):
    """Open the .png file from cloud storage and return it in buffer.

    It must have been previously uploaded to Firebase Cloud Storage under the name
    logo_{empresa_id}.png
    """
    logo_name = f"logo_{empresa_id}.png"
    bucket_file = _read_from_bucket(logo_name, bucket_name)
    logo_base64 = base64.b64encode(bucket_file).decode()
    return logo_base64


def certificate_file(empresa_id: str):
    """Open the .pfx file and return it in requests format"""

    certificate_name = f"CERTIF{empresa_id}.pfx"
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


def create_and_upload_pdf_from_html_string(
    empresa_id,
    html_string,
    firebase_bucket_name,  # parameter just for now
    count=0,
):
    """Create a PDF file from a HTML string and return the public URL."""
    filename = f"DTE_GD_{empresa_id}f{count}.pdf"
    pdf_bytes = HTML(string=html_string).write_pdf()
    url = _upload_to_bucket(pdf_bytes, filename, firebase_bucket_name, file_type="pdf")
    return url


def upload_xml_string_to_bucket(
    empresa_id,
    xml_string,
    document_type,
    firebase_bucket_name,  # parameter just for now
    count=0,
    id="",
):
    """
    Convert the XML string into a XML object, upload it to the bucket
    and return the public URL.
    """
    # tree = ET.XML(xml_string)
    tree = ET.fromstring(bytes(xml_string, encoding="latin1"))
    if document_type == "CAF":
        filename = f"CAF{empresa_id}n{count}.xml"
    elif document_type == "GD":
        filename = f"DTE_GD_{empresa_id}f{count}.xml"
    elif document_type == "SOBRE":
        filename = f"SOBRE_{id}.xml"

    string = ET.tostring(tree, encoding="latin1")
    url = _upload_to_bucket(string, filename, firebase_bucket_name, file_type="xml")
    return url


def _upload_to_bucket(file_to_upload, file_name, bucket_name, file_type="xml"):
    """Upload the XML file to the bucket and return the public URL."""

    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(file_name)
    # This is to avoid the caching of the file, which makes the file not to be updated
    # when the same file name is used.
    blob.cache_control = "no-cache, max-age=0"
    blob.upload_from_string(file_to_upload, content_type=f"application/{file_type}")
    blob.make_public()
    return blob.public_url


def _read_from_bucket(file_name, bucket_name):
    """Read the XML file from the bucket and return it in buffer."""

    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(file_name)
    bucket_file = blob.download_as_bytes()
    return bucket_file
