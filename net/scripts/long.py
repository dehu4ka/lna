from lna.taskapp.celery_app import app
import time, logging
from celery import current_task, shared_task, states
from net.lib import update_job_status


log = logging.getLogger(__name__)


@shared_task(bind=True)
def start(self, *args, **kwargs):
    RANGE = 60  # how long it will be runs
    for i in range(RANGE):
        time.sleep(1)
        log.debug('Tick %s of %s' % (str(i), str(RANGE)))
        self.update_state(states.STARTED, meta={'current': i, 'total': RANGE})
        message_to_user = "current: %s, total: %s" % (str(i), str(RANGE))
        update_job_status(self.request.id, state=states.STARTED, meta={'current': i, 'total': RANGE}, message=message_to_user)
    # meta is JSON field, it cant' be empty
    update_job_status(self.request.id, state=states.SUCCESS, result='My Mega Long Result', message='DONE!')
    self.update_state(states.SUCCESS)
    return {"status": "Long Task completed", "num_of_seconds": RANGE}
