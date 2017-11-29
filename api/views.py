from django.contrib.auth.models import User, Group
from django.http import Http404
from rest_framework.response import Response
from argus.models import ASTU
from rest_framework import viewsets, status
from api.serializers import NESerializer, ListVendorsSerializer, ListModelsSerializer, JobModelSerializer, \
    NEDetailsSerializer
from net.models import Job, Equipment
from lna.taskapp.celery_app import app
from rest_framework.views import APIView
from net.lib import discover_vendor
from net.equipment.generic import GenericEquipment


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

    """def destroy(self, request, *args, **kwargs):
        self.partial_update(request, *args, **kwargs)
        super(ListTasks, self).destroy(request, *args, **kwargs)

"""


class NEDetail(APIView):
    def get_object(self, pk):
        try:
            return Equipment.objects.get(pk=pk)
        except Equipment.DoesNotExist:
            raise Http404

    def get(self, request, pk, *args, **kwargs):
        """ Refreshing NE details and returns it's serializer """
        equipment = self.get_object(pk)
        generic_equipment = GenericEquipment(equipment_object=equipment)
        if generic_equipment.suggest_login(resuggest=False):
            # Trying to login only if login guessing was successful
            generic_equipment.do_login()
            if generic_equipment.discover_vendor():
                generic_equipment.get_config()
            generic_equipment.disconnect()

        serializer = NEDetailsSerializer(equipment)
        return Response(serializer.data)
