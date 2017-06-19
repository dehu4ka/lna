import time, logging
from lna.taskapp.celery import app

log = logging.getLogger(__name__)


@app.task()
def long_job(job_id, reply_channel):
    for i in range(3):
        log.debug("Tick " + str(i))
        print("Tick " + str(i))
        time.sleep(3)

    pass
