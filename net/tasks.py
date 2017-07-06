import time
import json
import logging
import subprocess
from celery import current_task, shared_task, states
from celery.exceptions import TaskRevokedError, WorkerShutdown, WorkerTerminate
from channels import Group
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from lna.taskapp.celery_app import app
from net.equipment.generic import b2a, GenericEquipment
from argus.models import ASTU
from net.models import Job, JobResult, Equipment
from time import sleep

log = logging.getLogger(__name__)


def update_job_status(celery_id, state=None, meta=None, result=None, message=None):
    job_exists = False  # Job in DB doesn't appears instantly. So we need somehow handle that behavior
    while not job_exists:
        try:
            job = Job.objects.get(celery_id=celery_id)
            job_exists = True
        except ObjectDoesNotExist:
            log.warning('update_job_status: Job object still not exists, sleeping 1 sec')
            time.sleep(1)
    if state:
        job.status = state
        if state == 'SUCCESS':
            job.completed = timezone.now()

    # if meta arg is exists, we put in db and later send job/task status update
    if meta:
        job.meta = meta
    else:
        # assuming that work is completed
        meta = {'current': 100, 'total': 100, }
        job.meta = meta

    job.save()
    if result:
        job_result, created = JobResult.objects.get_or_create(job_id=job)
        job_result.result += result  # adding result
        job_result.save()
    Group("task_watcher_%s" % str(job.id)).send(
        {"text": json.dumps({
            "script_name": job.script.name,
            "meta": {
                "current": meta['current'],
                "total": meta['total'],
            },
            "result": result,
            'result_update': message
        })}
    )


def scan_nets_with_fping_task_version(subnets):
    # test to avoid double import
    found, new = 0, 0  # Found Alive IP's and created ones
    for subnet in subnets:
        print(subnet)
        proc = subprocess.Popen(["/sbin/fping -O 160 -a -q -r 0 -g %s" % subnet], shell=True, stdout=subprocess.PIPE)
        proc.wait()
        out = proc.stdout.read()
        alive_list = out.decode().split('\n')[:-1]  # everything but the last empty
        for ip in alive_list:
            obj, created = Equipment.objects.get_or_create(ne_ip=ip.split(' ')[0])
            found += 1
            if created:
                new += 1
    return found, new


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


def get_destination_ips_list(destination_ids):
    """
    Function to get IP addresses from NE id's list.
    :param destination_ids: ['100', '200', ...]
    :return: ['10.205.18.1', 10.205.18.2', ...]
    """
    return [ASTU.objects.get(pk=ne_id).ne_ip for ne_id in destination_ids]  # list of IPs


@app.task(bind=True)
def login_suggest_task(self, destination_ids):
    log.info('celery task in login_suggest.py')
    total = len(destination_ids)
    update_job_status(self.request.id, state=states.STARTED, meta={'current': 0, 'total': total},
                      message='Login Suggest task was started')
    i = 1  # counter for updating progress
    task_result = ""  # After-all result of discovering credentials
    for target_id in destination_ids:  # getting ID
        try:
            astu_object = ASTU.objects.get(pk=target_id)  # getting ASTU object
            # Getting or creating Equipment object with IP-address of ASTU object
            eq_obj, created = Equipment.objects.get_or_create(ne_ip=astu_object.ne_ip)
            eq = GenericEquipment(eq_obj)
            result = eq.suggest_login(resuggest=False)  # dict
            if result:
                result_to_send = "<br>[%s]Discovered credentials, L: %s, P: %s" % \
                                 (result['ip'], result['login'], result['password'])
                task_result += "<br>[%s]Discovered credentials, L: %s, P: %s" % \
                               (result['ip'], result['login'], result['password'])
            else:
                result_to_send = "<br>Failed to discover credentials for %s" % (astu_object.ne_ip, )
                task_result += "<br>Failed to discover credentials for %s" % (astu_object.ne_ip, )
            update_job_status(self.request.id, state=states.STARTED, meta={'current': i, 'total': total},
                              message=result_to_send)
            i += 1
        except TaskRevokedError:
            log.error("TASK WAS REVOKED!")
            break
        except WorkerShutdown:
            log.error("WORKER WAS Shutdowned!")
            break
        except WorkerTerminate:
            log.error("WORKER WAS Terminated!")
            break
    update_job_status(self.request.id, state=states.SUCCESS, result=task_result, message='DONE!')
    return task_result


@app.task(bind=True)
def ping_task(self, destination_ids, **kwargs):
    log.warning("celery task in ping.py ")
    update_job_status(self.request.id, state=states.STARTED, meta={'current': 0, 'total': len(destination_ids)},
                      message='ping task was started')
    targets = get_destination_ips_list(destination_ids)
    targets = " ".join(targets)  # string with space separated IPs
    proc = subprocess.Popen(["/sbin/fping %s" % targets], shell=True, stdout=subprocess.PIPE)
    proc.wait()
    out = b2a(proc.stdout.read())  # convert from binary to ascii
    out = out.replace("\n", "<br>\n")  # some html breaks
    update_job_status(self.request.id, state=states.SUCCESS, result=out, message='DONE!')


@app.task(bind=True)
def long_job_task(self, *args, **kwargs):
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


@app.task(bind=True)
def celery_scan_nets_with_fping(self, subnets=('',)):
    """
    Task for scan subnets with fping
    :param self:
    :param subnets: list (or tuple, or iterable) with subnets, eg ['10.205.0.0/24', '10.205.1.0/24', ...]
    :return:
    """
    log.warning("celery task in celery_scan_nets_with_fping")
    update_job_status(self.request.id, state=states.STARTED, meta={'current': 0, 'total': len(subnets)},
                      message='ping task was started')
    found, new, subnet_counter, result = 0, 0, 0, ''  # counters of alive hosts and loop below counter
    for subnet in subnets:
        current_found, current_new = scan_nets_with_fping_task_version(list((subnet, )))  # we send only one subnet to func,
        # so we can update task status
        # Everything actually work makes 'scan_nets_with_fping', it will be found alive hosts and put new hosts to DB
        # So we need only to update task status:
        subnet_counter += 1
        found += current_found
        new += current_new
        result += "<br>\n" + 'Scan of %s result: %s alive, %s new hosts' % (subnet, current_found, current_new)
        update_job_status(self.request.id, state=states.STARTED,
                          meta={'current': subnet_counter, 'total': len(subnets)},
                          message='Scan of %s result: %s alive, %s new hosts' % (subnet, current_found, current_new))
    # After loop end:
    update_job_status(self.request.id, state=states.SUCCESS, result=result)
