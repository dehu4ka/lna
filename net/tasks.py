import time, logging
from lna.taskapp.celery import app
from argus.models import ASTU
from .models import Scripts
import importlib

log = logging.getLogger(__name__)


@app.task()
def long_job(job_id, reply_channel):
    for i in range(3):
        log.info("Tick " + str(i))
        print("Tick " + str(i))
        time.sleep(3)

    pass

@app.task()
def job_starter(ne_id, script_id):
    ne_obj = ASTU.objects.get(pk=ne_id)
    script_obj = Scripts.objects.get(pk=script_id)
    task_module = importlib.import_module(script_obj.class_name)
    result = task_module.start(target=ne_obj.ne_ip)
    log.info("Doing " + script_obj.name + ' for ' + ne_obj.ne_ip + '. Result was: ' + str(result))
    return result
