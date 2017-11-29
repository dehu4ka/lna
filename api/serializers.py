from rest_framework.fields import SerializerMethodField
from argus.models import ASTU
from rest_framework import serializers
from net.models import Job, Equipment, EquipmentConfig
from net.lib import HighlightRenderer
from mistune import Markdown


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


class NEDetailsSerializer(serializers.ModelSerializer):
    login = serializers.CharField(source='credentials.login')
    passw = serializers.CharField(source='credentials.passw')

    class Meta:
        model = Equipment
        fields = ('id', 'hostname', 'vendor', 'model', 'ne_ip', 'credentials_id', 'sw_version', 'login', 'passw',
                  'current_config')


class ArchiveConfigSerializer(serializers.ModelSerializer):
    colored_config = SerializerMethodField()

    class Meta:
        model = EquipmentConfig
        fields = ('colored_config', )

    def get_colored_config(self, obj):
        config = '```pre\n' + obj.config + '\n```'
        renderer = HighlightRenderer()
        markdown = Markdown(renderer=renderer)
        return markdown.render(config)
