import time, logging
from lna.taskapp.celery import app
from argus.models import ASTU
from net.models import Scripts, OnlineStatus
import importlib
import subprocess

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


@app.task()
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
    OnlineStatus.objects.all().delete()
    for alive_ip in alive_list:
        OnlineStatus.objects.update_or_create(status='ONLINE', astu=ASTU.objects.get(ne_ip=alive_ip))
