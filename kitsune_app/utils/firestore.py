from kitsune_app.setup.firebase import firestore_client

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

import base64


# NOT SURE OF ITS FINAL USAGE MAYBE IT WILL HAVE TO BE CHANGED
def _decrypt_password(encrypted_password, salt):
    """
    Utilizes the cryptography library with the Fernet algorithm to decrypt the password.
    Depends on the SALT .env
    """

    password_key = b"pass"
    salt = salt.encode()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=39000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password_key))
    f = Fernet(key)
    return f.decrypt(encrypted_password).decode()

def get_certificate_credentials(empresa_id: str, salt) -> dict:
    """ Gets the pfx certificate credentials from firestore """
    # Maybe it should create a new client each time for paralelism
    db = firestore_client()
    doc_ref = db.collection(u'credenciales_pfx').where(u'empresa_id', u'==', empresa_id).limit(1)
    docs = doc_ref.get()
    doc = docs[0].to_dict()
    pfx_certificate_credentials = {
            "RutCertificado": doc["rut_certificado"],
            "Password": _decrypt_password(doc["password"].encode(),salt),
        }
    return pfx_certificate_credentials