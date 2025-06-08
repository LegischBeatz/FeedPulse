from celery import Celery
app = Celery('feedpulse', broker='redis://redis:6379/0')

from . import tasks
