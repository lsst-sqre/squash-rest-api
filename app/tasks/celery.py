"""Initialize Celery to run background tasks.

See https://blog.miguelgrinberg.com/post/using-celery-with-flask
"""

import os

from celery import Celery

CELERY_BROKER_URL = os.environ.get(
    "CELERY_BROKER_URL", "redis://localhost:6379"
)

celery = Celery(__name__, backend=CELERY_BROKER_URL, broker=CELERY_BROKER_URL)
