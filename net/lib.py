from argus.models import ASTU
from django.core import serializers
import json

from rest_framework import serializers

class NESerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ASTU
        fields = ('hostname', 'ne_ip', 'vendor', 'model', 'status', )
