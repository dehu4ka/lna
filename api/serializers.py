from argus.models import ASTU
from rest_framework import serializers

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
