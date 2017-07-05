import json
from django.utils import timezone
from channels import Group
from net.tasks import ping_task, login_suggest_task, long_job_task
from net.models import Job, JobResult, Scripts
from argus.models import ASTU


def update_job_status(celery_id, state=None, meta=None, result=None, message=None):
    job = Job.objects.get(celery_id=celery_id)
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
        job_result.result = result
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


def starter(destinations_ids, script_id):
    job = Job()
    job.script = Scripts.objects.get(id=script_id)
    if script_id == '1':
        # ping
        ping_task.delay(destinations_ids[0])
    if script_id == '2':
        task = long_job_task.delay()
    if script_id == '3':
        task = login_suggest_task.delay(destinations_ids)
    job.celery_id = task.task_id
    job.status = 'PENDING'
    job.save()
    for ne in destinations_ids:
        job.ne_ids.add(ASTU.objects.get(pk=ne))
    job.save()

    pass
