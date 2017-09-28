import json
from django.utils import timezone
from django.db import transaction
from channels import Group
from net.equipment.generic import GenericEquipment
from net.tasks import ping_task, login_suggest_task, long_job_task, celery_scan_nets_with_fping, celery_discover_vendor
from net.models import Job, JobResult, Scripts, Equipment
from argus.models import ASTU
import subprocess


@transaction.non_atomic_requests
def celery_job_starter(destinations_ids, script_id):
    """
    Starts celery job

    :param destinations_ids:
    :param script_id:
    :return:
    """
    if destinations_ids == list():
        return False
    job = Job()  # new Job model object

    job.script = Scripts.objects.get(id=script_id)  # getting related Script object'

    if script_id == '1':
        # ping
        task = ping_task.delay(destinations_ids)
    elif script_id == '2':
        task = long_job_task.delay()
    elif script_id == '3':
        task = login_suggest_task.delay(destinations_ids)
    elif script_id == '999':
        task = celery_scan_nets_with_fping.delay(subnets=destinations_ids)
        destinations_ids = list()  # Empty list. We don't need to pick ASTU id's for discovery task
    elif script_id == '1000':
        task = celery_discover_vendor.delay(subnets=destinations_ids)
        destinations_ids = list()  # Empty list. We don't need to pick ASTU id's for discovery task
    else:
        return False
    job.celery_id = task.task_id
    job.status = 'PENDING'
    job.save()
    for ne in destinations_ids:
        job.ne_ids.add(ASTU.objects.get(pk=ne))
    job.save()

    pass


def scan_nets_with_fping(subnets):
    found, new = 0, 0  # Found Alive IP's and created ones
    for subnet in subnets:
        proc = subprocess.Popen(["/sbin/fping -O 160 -a -q -r 0 -g %s" % subnet], shell=True, stdout=subprocess.PIPE)
        proc.wait()
        out = proc.stdout.read()
        alive_list = out.decode().split('\n')[:-1]  # everything but the last empty
        for ip in alive_list:
            obj, created = Equipment.objects.get_or_create(ne_ip=ip.split(' ')[0])
            found += 1
            if created:
                new += 1
                obj.hostname = None
                obj.vendor = None
                obj.model = None
                obj.save()
    return found, new


def discover_vendor(subnets):
    """
    Does network element discovery and finds logins/passwords from credentials database

    :param subnets: list with subnets to discover

    :return: login_suggest_success_count, vendor_found_count

    """
    login_suggest_success_count = 0
    vendor_found_count = 0
    for subnet in subnets:
        # If we can't find "/" (slash) symbol in subnets, than user had entered the host only, and no subnet
        if subnet.find("/") == -1:
            # one host
            hosts = Equipment.objects.filter(ne_ip=subnet)
        else:
            # subnet
            hosts = Equipment.objects.filter(ne_ip__net_contained=subnet)
        for host in hosts:
            eq = GenericEquipment(host)
            # need to adjust it? or 1 sec is enough?
            eq.set_io_timeout(1)
            if eq.suggest_login(resuggest=False):
                login_suggest_success_count += 1
                # Trying to login only if login guessing was successful
                eq.do_login()
                if eq.discover_vendor():
                    vendor_found_count += 1
                eq.disconnect()
    return login_suggest_success_count, vendor_found_count
