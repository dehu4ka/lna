from argus.models import ASTU
from django.core import serializers
import json
from net.models import Job, JobResult
from django.utils import timezone
from channels import Group


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
    if meta:
        job.meta = meta
    else:
        job.meta = ''
    job.save()
    if result:
        job_result, created = JobResult.objects.get_or_create(job_id=job)
        job_result.result = result
        job_result.save()
    Group("task_watcher_%s" % str(job.id)).send(
        {"text": json.dumps({
            "script_name": job.script_name,
            "meta": {
                "current": meta.current,
                "total": meta.total,
            },
            "result": result
        })}
    )


