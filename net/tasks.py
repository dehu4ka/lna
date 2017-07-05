import time
import logging
from argus.models import ASTU
import subprocess
from celery import current_task, shared_task, states
from lna.taskapp.celery_app import app

log = logging.getLogger(__name__)


@shared_task
def long_job(job_id, reply_channel):
    for i in range(3):
        log.info("Tick " + str(i))
        print("Tick " + str(i))
        time.sleep(3)

    pass



@shared_task
def check_online():
    """
    Checking NE status with FPING
    :return:
    """
    ne_objects = ASTU.objects.all().filter(status='эксплуатация')
    fping_ips_str = ''  # ip addresses separated by space for fping
    for ne in ne_objects:
        fping_ips_str += str(ne.ne_ip) + " "
    #  Type of service = 160, only alive, quiet, zero repeat
    proc = subprocess.Popen(["/sbin/fping -O 160 -a -q -r 0 %s" % fping_ips_str], shell=True, stdout=subprocess.PIPE)
    proc.wait()
    out = proc.stdout.read()
    alive_list = out.decode().split('\n')[:-1]  # everything but the last empty
    ASTU.objects.all().update(is_online=False)
    for alive_ip in alive_list:
        obj = ASTU.objects.get(ne_ip=alive_ip)
        obj.is_online = True
        obj.save()
    return {'status': 'Completed', 'alive_objects': len(alive_list)}


@shared_task
def login_suggest_task(self):
    log.warning('celery task in login_suggest.py')


@shared_task
def ping_task(target='127.0.0.1', **kwargs):
    log.warning("celery task in ping.py")


@app.task(bind=True)
def long_job_task(self, *args, **kwargs):
    try:
        from net.lib import update_job_status
    except:
        pass
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


