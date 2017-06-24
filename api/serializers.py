from argus.models import ASTU
from rest_framework import serializers
from net.models import OnlineStatus

class NESerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ASTU
        fields = ('id', 'hostname', 'ne_ip', 'vendor', 'model', 'status', )


class ListVendorsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ASTU
        fields = ('vendor', )

class ListModelsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ASTU
        fields = ('vendor', 'model', )

class OnlineStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnlineStatus
        fields = ('astu_id', 'status')
