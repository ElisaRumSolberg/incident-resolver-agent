from functools import lru_cache

from google.cloud import firestore

from app.config import settings


@lru_cache
def get_firestore_client() -> firestore.Client:
    return firestore.Client(
        project=settings.google_cloud_project or None,
        database=settings.firestore_database,
    )
