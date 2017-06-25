from lna.taskapp.celery import app
import time, logging
from celery import current_task, shared_task, states

log = logging.getLogger(__name__)


@shared_task
def start(*args, **kwargs):
    for i in range(30):
        time.sleep(1)
        log.warning('Tick %s of 10' % str(i))
        current_task.update_state(states.STARTED, meta={'current': i, 'total': 10})
    return True
