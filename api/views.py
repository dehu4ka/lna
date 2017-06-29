from django.contrib.auth.models import User, Group
from rest_framework.response import Response
from argus.models import ASTU
from rest_framework import viewsets, status
from api.serializers import NESerializer, ListVendorsSerializer, ListModelsSerializer, JobModelSerializer
from net.models import Job
from lna.taskapp.celery_app import app


class NEViewSet(viewsets.ModelViewSet):
    queryset = ASTU.objects.all().order_by('id').filter(status='эксплуатация')
    serializer_class = NESerializer


class ListVendors(viewsets.ModelViewSet):
    queryset = ASTU.objects.all().order_by('vendor').distinct('vendor')
    serializer_class = ListVendorsSerializer


class ListModels(viewsets.ModelViewSet):
    queryset = ASTU.objects.all().order_by('model').distinct('model')
    serializer_class = ListModelsSerializer


class ListTasks(viewsets.ModelViewSet):
    queryset = Job.objects.all()
    serializer_class = JobModelSerializer

    # PATCH Method we are using to terminate task
    def partial_update(self, request, *args, **kwargs):
        task_id = request.data['task_id']
        job = Job.objects.get(pk=task_id)  # Job Object Related
        if job.status == 'STARTED' or job.status == 'PENDING':  # работающие или планируемые к запуску задачи
            app.control.revoke(job.celery_id, terminate=True, signal='SIGKILL')
            job.status = 'TERMINATED'
            job.save()

        return Response(status=status.HTTP_202_ACCEPTED, data='test')

