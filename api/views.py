from django.contrib.auth.models import User, Group
from argus.models import ASTU
from rest_framework import viewsets
from .serializers import NESerializer, ListVendorsSerializer, ListModelsSerializer

class NEViewSet(viewsets.ModelViewSet):
    queryset = ASTU.objects.all().order_by('id').filter(status='эксплуатация')
    serializer_class = NESerializer


class ListVendors(viewsets.ModelViewSet):
    queryset = ASTU.objects.all().order_by('vendor').distinct('vendor')
    serializer_class = ListVendorsSerializer


class ListModels(viewsets.ModelViewSet):
    queryset = ASTU.objects.all().order_by('model').distinct('model')
    serializer_class = ListModelsSerializer