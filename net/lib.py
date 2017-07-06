import json
from django.utils import timezone
from channels import Group
from net.tasks import ping_task, login_suggest_task, long_job_task
from net.models import Job, JobResult, Scripts
from argus.models import ASTU




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
