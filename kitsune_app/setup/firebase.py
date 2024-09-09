from contextvars import ContextVar

from kitsune_app.settings import FIREBASE_BUCKET

import firebase_admin
import firebase_admin.firestore
import firebase_admin.storage

import google.cloud.firestore
import google.cloud.storage


db = ContextVar("Firestore_Database_Client")
bucket = ContextVar("Firebase_Storage_Client")


def get_firestore_client() -> google.cloud.firestore.Client:
    """
    Returns the firestore database client in the actual context.

    Not sure if this is the best approach, maybe using multiple clients for paralelism
    would be better.
    """
    return db.get()


def get_firebase_storage_bucket() -> google.cloud.storage.Bucket:
    """
    Returns the default firebase storage client in the actual context.
    """
    return bucket.get()


def firebase_setup():
    """
    Initializes everything regarding firebase setup, function to be called once in main
    """
    firebase_admin.initialize_app(options={"storageBucket": f"{FIREBASE_BUCKET}"})
    _db = firebase_admin.firestore.client()
    db.set(_db)
    _bucket = firebase_admin.storage.bucket()
    bucket.set(_bucket)
