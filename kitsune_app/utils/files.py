import base64

import lxml.etree as ET

from weasyprint import HTML  # type: ignore

from kitsune_app.setup.firebase import get_firebase_storage_bucket


def get_xml_file_tuple_for_request(
    empresa_id,
    file_type,
    CAF_step=0,
    DTE_type="GD",
    folio_or_sobre_count=0,
    id="",
    file_tuple_name="file",
    version=0,  # This is only for the DTE that are repetidos
):
    """Open the .xml file from cloud storage and return it in buffer.
    Keep in mind that the CAF_step must be sync with the ObtainFoliosIn.amount in dte.py
    """
    if file_type == "CAF" and (DTE_type == "GD" or DTE_type == "FA"):
        CAF_number = (folio_or_sobre_count - 1) // CAF_step
        file_name = f"empresas/{empresa_id}/CAF/{DTE_type}/{CAF_number}.xml"
    elif file_type == "DTE" and (DTE_type == "GD" or DTE_type == "FA"):
        file_name = f"empresas/{empresa_id}/DTE/{DTE_type}/{folio_or_sobre_count}.xml"
        # Add the version to the DTE filename if it is > 0
        if version > 0:
            # Alter the filename to include the version number right before the extension .xml
            file_name = file_name.replace(".xml", f"_{version}.xml")
    elif file_type == "SOBRE":
        file_name = f"empresas/{empresa_id}/SOBRES/{id}.xml"

    bucket_file = _read_from_bucket(file_name)

    _filename_for_simpleAPI = file_name.split("/")[-1]

    file_file = (
        file_tuple_name,
        (
            _filename_for_simpleAPI,
            bucket_file,
            "text/xml",
        ),
    )
    return file_file


def get_logo_base64(empresa_id: str):
    """Open the .png file from cloud storage and return it in buffer.

    It must have been previously uploaded to Firebase Cloud Storage under the name
    logo_{empresa_id}.png
    """
    logo_file_name = f"empresas/{empresa_id}/logo.png"
    logo_file = _read_from_bucket(logo_file_name)
    logo_base64 = base64.b64encode(logo_file).decode()
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


def create_and_upload_pdf(
    empresa_id,
    pdf_content,
    DTE_type="GD",
    count=0,
    version=0,  # This is only for the DTE that are repetidos
    from_string=True,
):
    """Create a PDF from a HTML string and return the file name within its bucket."""
    filename = f"empresas/{empresa_id}/DTE/{DTE_type}/{count}.pdf"
    if version > 0:
        filename = filename.replace(".pdf", f"_{version}.pdf")
    if from_string:
        pdf_bytes = HTML(string=pdf_content).write_pdf()
    else:
        pdf_bytes = pdf_content

    file_name_in_bucket = _upload_to_bucket(pdf_bytes, filename, file_type="pdf")
    return file_name_in_bucket


def upload_xml_string_to_bucket(
    empresa_id,
    xml_string,
    document_type,
    DTE_type="GD",
    count=0,
    id="",
    version=0,  # This is only for the DTE that are repetidos
):
    """
    Convert the XML string into a XML object, upload it to the bucket
    and return the file name within its bucket.
    """
    tree = ET.fromstring(bytes(xml_string, encoding="latin1"))
    if document_type == "CAF" and (DTE_type == "GD" or DTE_type == "FA"):
        filename = f"empresas/{empresa_id}/CAF/{DTE_type}/{count}.xml"
    elif document_type == "DTE" and (DTE_type == "GD" or DTE_type == "FA"):
        filename = f"empresas/{empresa_id}/DTE/{DTE_type}/{count}.xml"
        # Add the version to the DTE filename if it is > 0
        if version > 0:
            # Alter the filename to include the version number right before the extension .xml
            filename = filename.replace(".xml", f"_{version}.xml")
    elif document_type == "SOBRE":
        filename = f"empresas/{empresa_id}/SOBRES/{id}.xml"

    string = ET.tostring(tree, encoding="latin1")
    xml_filename_in_bucket = _upload_to_bucket(string, filename, file_type="xml")
    return xml_filename_in_bucket


def _upload_to_bucket(file_to_upload, file_name, file_type="xml"):
    """Upload the XML file to the bucket and return the file name within its bucket."""

    bucket = get_firebase_storage_bucket()
    blob = bucket.blob(file_name)
    # This is to avoid the caching of the file, which makes the file not to be updated
    # when the same file name is used.
    blob.cache_control = "no-cache, max-age=0"
    blob.upload_from_string(file_to_upload, content_type=f"application/{file_type}")
    return file_name


# Now with Firebase
def _read_from_bucket(file_name):
    """Read the XML file from the bucket and return it in buffer."""

    bucket = get_firebase_storage_bucket()
    blob = bucket.blob(file_name)
    bucket_file = blob.download_as_bytes()
    return bucket_file


# Previously with GCP directly
# def _read_from_bucket(file_name, bucket_name):
#     """Read the XML file from the bucket and return it in buffer."""

#     storage_client = storage.Client()
#     bucket = storage_client.get_bucket(bucket_name)
#     blob = bucket.blob(file_name)
#     bucket_file = blob.download_as_bytes()
#     return bucket_file
