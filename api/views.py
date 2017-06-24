from django.contrib.auth.models import User, Group
from argus.models import ASTU
from net.models import OnlineStatus
from rest_framework import viewsets
from api.serializers import NESerializer, ListVendorsSerializer, ListModelsSerializer, OnlineStatusSerializer

class NEViewSet(viewsets.ModelViewSet):
    queryset = ASTU.objects.all().order_by('id').filter(status='эксплуатация')
    serializer_class = NESerializer


class ListVendors(viewsets.ModelViewSet):
    queryset = ASTU.objects.all().order_by('vendor').distinct('vendor')
    serializer_class = ListVendorsSerializer


class ListModels(viewsets.ModelViewSet):
    queryset = ASTU.objects.all().order_by('model').distinct('model')
    serializer_class = ListModelsSerializer

class OnlineStatusREST(viewsets.ModelViewSet):
    queryset = OnlineStatus.objects.all().order_by('astu_id')
    serializer_class = OnlineStatusSerializer
