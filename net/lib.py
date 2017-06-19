from argus.models import ASTU
from django.core import serializers

def get_ne_json():
    """
    Selects from argus NE's and returns JSON data
    :return:
    """
    json = serializers.serialize('json', ASTU.objects.all().filter(hostname='89-BLYARS-ACC4220-ACSW-1'))
    print(json.encode('utf8'))
    return json
