from django.db import models

# Create your models here.
class ArgusADSL(models.Model):
    city = models.CharField(max_length=512, default='N/A')
    hostname = models.CharField(max_length=512, default='None')
    ne_ip = models.GenericIPAddressField(protocol='IPv4', default='0.0.0.0')
    tel_num = models.CharField(default='', max_length=16, db_index=True)
    address = models.CharField(max_length=512, default='N/A')
    fio = models.CharField(max_length=512, default='N/A')
    room = models.CharField(max_length=512, default='N/A')
    iptv_login = models.CharField(max_length=512, db_index=True)
    inet_login = models.CharField(max_length=512, db_index=True)
    slot = models.CharField(max_length=512, default='N/A')
    port = models.CharField(max_length=512, default='N/A')
    lira = models.CharField(max_length=32, default='N/A')


class ArgusFTTx(models.Model):
    city = models.CharField(max_length=512, default='N/A')
    hostname = models.CharField(max_length=512, default='None')
    ne_ip = models.GenericIPAddressField(protocol='IPv4', default='0.0.0.0')
    tel_num = models.CharField(default='', max_length=16, db_index=True)
    address = models.CharField(max_length=512, default='N/A')
    fio = models.CharField(max_length=512, default='N/A')
    room = models.CharField(max_length=512, default='N/A')
    iptv_login = models.CharField(max_length=512, db_index=True)
    inet_login = models.CharField(max_length=512, db_index=True)
    slot = models.CharField(max_length=512, default='N/A')
    port = models.CharField(max_length=512, default='N/A')
    lira = models.CharField(max_length=32, default='N/A')


class ArgusGPON(models.Model):
    city = models.CharField(max_length=512, default='N/A')
    hostname = models.CharField(max_length=512, default='None')
    ne_ip = models.GenericIPAddressField(protocol='IPv4', default='0.0.0.0')
    tel_num = models.CharField(default='', max_length=16, db_index=True)
    address = models.CharField(max_length=512, default='N/A')
    fio = models.CharField(max_length=512, default='N/A')
    room = models.CharField(max_length=512, default='N/A')
    iptv_login = models.CharField(max_length=512, db_index=True)
    inet_login = models.CharField(max_length=512, db_index=True)
    slot = models.CharField(max_length=512, default='N/A')
    port = models.CharField(max_length=512, default='N/A')
    lira = models.CharField(max_length=32, default='N/A')


# Common client model
class Client(models.Model):
    city = models.CharField(max_length=512, default='N/A')
    hostname = models.CharField(max_length=512, default='None')
    ne_ip = models.GenericIPAddressField(protocol='IPv4', default='0.0.0.0')
    tel_num = models.CharField(default='', max_length=16, db_index=True)
    address = models.CharField(max_length=512, default='N/A')
    fio = models.CharField(max_length=512, default='N/A')
    room = models.CharField(max_length=512, default='N/A')
    iptv_login = models.CharField(max_length=512, db_index=True)
    inet_login = models.CharField(max_length=512, db_index=True)
    slot = models.CharField(max_length=512, default='N/A')
    port = models.CharField(max_length=512, default='N/A')
    lira = models.CharField(max_length=32, default='N/A')
    tech = models.CharField(max_length=32, default='N/A')


class ASTU(models.Model):
    hostname = models.CharField(max_length=512, default='', unique=True, db_index=True)
    address = models.CharField(max_length=512, default='')
    structure_level = models.CharField(max_length=512, default='')
    ne_class = models.CharField(max_length=512, default='')  # class is python reserved word
    vendor = models.CharField(max_length=512, default='')
    model = models.CharField(max_length=512, default='')
    status = models.CharField(max_length=512, default='')
    comment = models.CharField(max_length=512, default='')
    ne_ip = models.GenericIPAddressField(protocol='IPv4', db_index=True)
    category = models.CharField(max_length=16, default='')
    segment = models.CharField(max_length=512, default='')
    serial_number = models.CharField(max_length=512, default='')

    def __str__(self):
        return self.hostname + " : " + self.ne_ip + " : " + self.vendor + " : " + self.model




