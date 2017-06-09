from django.db import models

# Create your models here.
class ArgusADSL(models.Model):
    city = models.CharField(max_length=512, default='N/A')
    hostname = models.CharField(max_length=512, default='None')
    ne_ip = models.GenericIPAddressField(protocol='IPv4', default='0.0.0.0')
    tel_num = models.BigIntegerField(default=-1, db_index=True)
    address = models.CharField(max_length=512, default='N/A')
    fio = models.CharField(max_length=512, default='N/A')
    room = models.CharField(max_length=512, default='N/A')
    iptv_login = models.CharField(max_length=512, db_index=True)
    inet_login = models.CharField(max_length=512, db_index=True)
    xdsl_slot = models.CharField(max_length=512, default='N/A')
    xdsl_port = models.CharField(max_length=512, default='N/A')

