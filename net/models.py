from django.db import models
from django.utils import timezone

# Create your models here.
class Job(models.Model):
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=255, null=True, blank=True)
    created = models.DateTimeField(default=timezone.now)
    completed = models.DateTimeField(null=True)
    celery_id = models.CharField(max_length=255)
    script_name = models.CharField(max_length=255, default='')
    ne_ip = models.GenericIPAddressField(protocol='IPv4', default='0.0.0.0')

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
