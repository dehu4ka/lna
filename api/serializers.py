from argus.models import ASTU
from rest_framework import serializers

class NESerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ASTU
        fields = ('id', 'hostname', 'ne_ip', 'vendor', 'model', 'status', )

