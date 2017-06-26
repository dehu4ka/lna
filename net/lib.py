from argus.models import ASTU
from django.core import serializers
import json
from net.models import Job, JobResult

from rest_framework import serializers

class NESerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ASTU
        fields = ('hostname', 'ne_ip', 'vendor', 'model', 'status', )


def update_job_status(celery_id=None, state=None, meta=None, result=None):
    job = Job.objects.get(celery_id=celery_id)
    if state:
        job.status = state
    if result:
        job_result = JobResult.objects.get_or_create(job_id=job)
        job_result.result = result
        job_result.save()
    if meta:
        job.meta = meta
    job.save()

