from django.http import Http404
from rest_framework.response import Response
from argus.models import ASTU
from rest_framework import viewsets, status
from api.serializers import NESerializer, ListVendorsSerializer, ListModelsSerializer, JobModelSerializer, \
    NEDetailsSerializer, ArchiveConfigSerializer
from net.models import Job, Equipment, EquipmentConfig
from lna.taskapp.celery_app import app
from rest_framework.views import APIView
from net.equipment.generic import GenericEquipment
from difflib import unified_diff
from mistune import Markdown
from pygments import highlight
from pygments.lexers.diff import DiffLexer
from pygments.formatters import HtmlFormatter
from rest_framework.permissions import AllowAny


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


class ArchiveConfig(APIView):
    def get_object(self, pk):
        try:
            return EquipmentConfig.objects.get(pk=pk)
        except EquipmentConfig.DoesNotExist:
            raise Http404

    def get(self, request, pk, *args, **kwargs):
        config = self.get_object(pk)
        config_serializer = ArchiveConfigSerializer(config)
        return Response(config_serializer.data)


class ConfigDiff(ArchiveConfig):
    def get(self, request, pk, pk2, *args, **kwargs):
        first_config = self.get_object(pk=pk).config.splitlines(keepends=True)
        second_config = self.get_object(pk=pk2).config.splitlines(keepends=True)
        first_date = self.get_object(pk=pk).updated.strftime('%d %b %Y %H:%M:%S')
        second_date = self.get_object(pk=pk2).updated.strftime('%d %b %Y %H:%M:%S')

        diff = unified_diff(first_config, second_config, fromfile=first_date, tofile=second_date)
        diff = list(diff)  # list
        diff = ''.join(diff)
        # diff = '<pre><code>' + diff + '</code></pre>'

        lexer = DiffLexer()
        formatter = HtmlFormatter()
        colored_diff = highlight(diff, lexer, formatter)

        answer = {
            'diff': colored_diff,
        }

        return Response(answer)


class IsPPPoEIAConfigured(APIView):
    """
    Does search for pppoe intermediate agent in config. Returns JSON with search result
    """
    permission_classes = (AllowAny, )

    def get(self, request, ip, *args, **kwargs):
        try:
            obj = Equipment.objects.get(ne_ip=ip)
        except Equipment.DoesNotExist:
            raise Http404
        config = obj.current_config
        if obj.model == 'S2309TP-EI' or obj.model == 'SNR-S2985G-8T' or obj.model == 'S3328TP-EI':
            if config.find('pppoe intermediate-agent') == -1:
                return Response({'configured': False})
            else:
                return Response({'configured': True})
        else:
            return Response({'configured': 'N/A'})


class ConfigSearch(APIView):
    """
    Does search for string in NE config. Returns JSON with search result
    """
    permission_classes = (AllowAny,)

    def get(self, request, ip, search, *args, **kwargs):
        try:
            obj = Equipment.objects.get(ne_ip=ip)
        except Equipment.DoesNotExist:
            raise Http404
        config = obj.current_config
        if config.find(search) == -1:
            return Response({'found': False})
        else:
            return Response({'found': True})
