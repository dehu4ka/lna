import json
from django.utils import timezone
from django.db import transaction
from channels import Group
from net.tasks import ping_task, login_suggest_task, long_job_task
from net.models import Job, JobResult, Scripts, Equipment
from argus.models import ASTU
import subprocess

@transaction.non_atomic_requests
def starter(destinations_ids, script_id):
    if destinations_ids == list():
        return False
    job = Job()  # new Job model object
    job.script = Scripts.objects.get(id=script_id)  # getting related Script object'
    if script_id == '1':
        # ping
        task = ping_task.delay(destinations_ids)
    elif script_id == '2':
        task = long_job_task.delay()
    elif script_id == '3':
        task = login_suggest_task.delay(destinations_ids)
    else:
        return False
    job.celery_id = task.task_id
    job.status = 'PENDING'
    job.save()
    for ne in destinations_ids:
        job.ne_ids.add(ASTU.objects.get(pk=ne))
    job.save()

    pass


def scan_nets_with_fping(subnets):
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
                print("New: ",  ip)
    return found, new
