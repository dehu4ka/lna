from django.db import models
from django.utils import timezone
from argus.models import ASTU
from django.contrib.postgres.fields import JSONField

# Create your models here.
class Job(models.Model):
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=255, null=True, blank=True)
    created = models.DateTimeField(default=timezone.now)
    completed = models.DateTimeField(null=True)
    celery_id = models.CharField(max_length=255)
    script_name = models.CharField(max_length=255, default='')
    ne_id = models.ForeignKey(ASTU, on_delete=models.CASCADE)
    meta = JSONField(default='')

    class Meta:
        ordering = ('created', )

    def __str__(self):
        return self.name


class JobResult(models.Model):
    job_id = models.ForeignKey(Job, on_delete=models.CASCADE)
    result = models.TextField(max_length=10000)


class Scripts(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(max_length=10000)
    class_name = models.CharField(max_length=255)
    possible_vendor = models.CharField(max_length=255)
    possible_model = models.CharField(max_length=255)

    class Meta:
        ordering = ('name', )


