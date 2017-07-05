from rest_framework.relations import PrimaryKeyRelatedField

from argus.models import ASTU
from rest_framework import serializers
from net.models import Job


class NESerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ASTU
        fields = ('id', 'hostname', 'ne_ip', 'vendor', 'model', 'status', 'is_online', )


class ListVendorsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ASTU
        fields = ('vendor', )


class ListModelsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ASTU
        fields = ('vendor', 'model', )


class JobModelSerializer(serializers.HyperlinkedModelSerializer):
    script_name = serializers.CharField(source='script.name')

    class Meta:
        model = Job
        fields = ('name', 'status', 'created', 'completed', 'celery_id', 'script_name', 'meta')
