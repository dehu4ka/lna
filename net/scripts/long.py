from lna.taskapp.celery_app import app
import time, logging
from celery import current_task, shared_task, states
from net.lib import update_job_status


log = logging.getLogger(__name__)


@shared_task(bind=True)
def start(self, *args, **kwargs):
    for i in range(30):
        time.sleep(1)
        log.warning('Tick %s of 10' % str(i))
        self.update_state(states.STARTED, meta={'current': i, 'total': 30})
        update_job_status(self.request.id, meta={'current': i, 'total': 30})
    self.update_state(states.SUCCESS)
    update_job_status(self.request.id, state=states.SUCCESS, meta=None)
    return {"status": "Long Task completed", "num_of_seconds": 30}
