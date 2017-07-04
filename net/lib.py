from argus.models import ASTU
from django.core import serializers
import json
from net.models import Job, JobResult, Scripts
from django.utils import timezone
from channels import Group
import importlib


from rest_framework import serializers

class NESerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ASTU
        fields = ('hostname', 'ne_ip', 'vendor', 'model', 'status', )


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
            "script_name": job.script_name,
            "meta": {
                "current": meta['current'],
                "total": meta['total'],
            },
            "result": result,
            'result_update': message
        })}
    )


def starter(ne_ids, script_id, **kwargs):
    """
    Will start script like a Celery job
    :param ne_ids: List with NE ids, currently from ASTU model
    :param script_id: Script ID, we will get it from DB
    :param kwargs: For future use
    :return:
    """
    script = Scripts.objects.get(id=script_id)
    task = importlib.import_module(script.class_name)
    # May later we need to do some work with **kwargs
    task.start.delay(ne_ids)



    pass
