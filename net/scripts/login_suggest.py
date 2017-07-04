from lna.taskapp.celery_app import app
from celery import current_task, shared_task, states
import logging

app.tasks.register(start)

log = logging.getLogger(__name__)

@shared_task(bind=True)
def start(self, ne_ids, **kwargs):
    log.info('login_suggest start')
    pass
