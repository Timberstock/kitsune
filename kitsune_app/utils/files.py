# from xml.etree import ElementTree as ET
from datetime import datetime
import lxml.etree as ET

from google.cloud import storage  # type: ignore


def get_xml_file_tuple_for_request(
    empresa_id, file_type, bucket_name, folio_or_sobre_count=0, CAF_step=5, date=None
):
    """Open the .xml file from cloud storage and return it in buffer"""
    if file_type == "CAF":
        CAF_number = (folio_or_sobre_count - 1) // CAF_step
        file_name = f"CAF{empresa_id}n{CAF_number}.xml"
    elif file_type == "GD":
        file_name = f"DTE_GD_{empresa_id}f{folio_or_sobre_count}.xml"
    elif file_type == "SOBRE":
        date = datetime.strptime(date, "%Y-%m-%d").date()
        file_name = f"SOBRE_{empresa_id}d{date.year}_{date.month}_{date.day}.xml"
    bucket_file = _read_from_bucket(file_name, bucket_name)

    # This seems to be a way of reading the file from the bucket similar to open()
    # bucket_file = io.BytesIO(_read_from_bucket(file_name, bucket_name))

    # The following code is for testing purposes only
    # bucket_file_2 = open("files/" + file_name, "rb").read()
    # print(bucket_file == bucket_file_2)
    # print(f"bucket_file: {bucket_file}")
    # print(f"bucket_file_2: {bucket_file_2}")
    # raise Exception("stop")

    file_file = (
        "file",
        (
            file_name,
            bucket_file,
            # open(
            #     "files/" + file_name,
            #     "rb",
            # ),
            "text/xml",
        ),
    )
    return file_file


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


def upload_xml_string_to_bucket(
    empresa_id,
    xml_string,
    document_type,
    firebase_bucket_name,  # parameter just for now
    count=0,
    date=None,
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
        filename = f"SOBRE_{empresa_id}d{date.year}_{date.month}_{date.day}.xml"

    string = ET.tostring(tree, encoding="latin1")
    url = _upload_to_bucket(string, filename, firebase_bucket_name)
    return url


def _read_from_bucket(file_name, bucket_name):
    """Read the XML file from the bucket and return it in buffer."""

    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(file_name)
    bucket_file = blob.download_as_bytes()
    return bucket_file


def _upload_to_bucket(file_to_upload, file_name, bucket_name):
    """Upload the XML file to the bucket and return the public URL."""

    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(file_name)
    blob.upload_from_string(file_to_upload, content_type="application/xml")
    blob.make_public()
    return blob.public_url
