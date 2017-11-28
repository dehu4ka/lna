from django.db import models
from django.utils import timezone
from argus.models import ASTU
from django.contrib.postgres.fields import JSONField
from netfields import InetAddressField, NetManager

# Create your models here.


class Scripts(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(max_length=10000)
    class_name = models.CharField(max_length=255)
    possible_vendor = models.CharField(max_length=255)
    possible_model = models.CharField(max_length=255)
    is_hidden = models.BooleanField(default=False)

    class Meta:
        ordering = ('name', )


class Job(models.Model):
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=255, null=True, blank=True)
    created = models.DateTimeField(default=timezone.now)
    completed = models.DateTimeField(null=True)
    celery_id = models.CharField(max_length=255)
    script = models.ForeignKey(Scripts, on_delete=models.CASCADE, null=True)
    ne_ids = models.ManyToManyField(ASTU)
    meta = JSONField(default='')

    class Meta:
        ordering = ('-created', )

    def __str__(self):
        return self.name


class JobResult(models.Model):
    job_id = models.ForeignKey(Job, on_delete=models.CASCADE)
    result = models.TextField(max_length=10000)


# Login/Pass/Enable credentials
class Credentials(models.Model):
    login = models.CharField(max_length=512, default='')
    passw = models.CharField(max_length=512, default='')
    enable_password = models.CharField(max_length=512, default='')
    snmp_community = models.CharField(max_length=512, default='')
    comment = models.CharField(max_length=512, default='')

    class Meta:
        ordering = ('id', )

    def __str__(self):
        return "Credentials: " + self.login + " / " + self.passw


# proven-info model class
class Equipment(models.Model):
    hostname = models.CharField(max_length=512, null=True, default=None)
    vendor = models.CharField(max_length=512, null=True, default=None)
    model = models.CharField(max_length=512, null=True, default=None)
    # ne_ip = models.GenericIPAddressField(protocol='IPv4', db_index=True, unique=True)
    ne_ip = InetAddressField(db_index=True, unique=True)
    credentials = models.ForeignKey(Credentials, on_delete=models.CASCADE, null=True)
    sw_version = models.CharField(max_length=512, null=True, default=None)  # software version
    telnet_port_open = models.BooleanField(default=False)
    current_config = models.TextField()

    objects = NetManager()

    def __str__(self):
        return "Equipment object with IP: " + str(self.ne_ip)


class EquipmentSuggestCredentials(models.Model):
    equipment_id = models.ForeignKey(Equipment, on_delete=models.CASCADE, null=True)  # Equipment foreign key
    credentials_id = models.ForeignKey(Credentials, on_delete=models.CASCADE, null=True)  # Credentials FK
    # True if was unsuccessful attempt to login equipment with provided credentials
    was_checked = models.BooleanField(default=False)

    class Meta:
        ordering = ('equipment_id', )


class EquipmentConfig(models.Model):
    equipment_id = models.ForeignKey(Equipment, on_delete=models.CASCADE, null=True)  # Equipment foreign key
    updated = models.DateTimeField(auto_now_add=True)  # when config was updated
    config = models.TextField()  # subj

    class Meta:
        ordering = ('-updated', )


class EquipmentPorts(models.Model):
    up_down_choices = (('Up', 'up'), ('Down', 'down'))
    equipment_id = models.ForeignKey(Equipment, on_delete=models.CASCADE, null=True)  # Equipment foreign key
    if_alias = models.CharField(max_length=256, null=True, default=None)  # alias, eq "FastEthernet0/3"
    if_name = models.CharField(max_length=256, null=True, default=None)  # name, eq "Fa0/3"
    # description, eq "To AMTS Server NIC2 at 203 room"
    if_descr = models.CharField(max_length=512, null=True, default=None)
    if_oper_status = models.CharField(max_length=4, choices=up_down_choices)  # operational status, up or down
    if_admin_status = models.CharField(max_length=4, choices=up_down_choices)  # administrative status, up or down
    if_speed = models.BigIntegerField(default=0)  # interface speed
    if_ip = InetAddressField()

    objects = NetManager()


class Subnets(models.Model):
    network = InetAddressField(db_index=True, unique=True)
    descr = models.CharField(max_length=256, default='')
    is_active = models.BooleanField(default=True)

    objects = NetManager()
