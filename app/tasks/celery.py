import os
from celery import Celery

CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL',
                                   'redis://localhost:6379')

celery = Celery(__name__, broker=CELERY_BROKER_URL)
