import json
from django.utils import timezone
from django.db import transaction
from channels import Group
from net.equipment.generic import GenericEquipment
from net.tasks import ping_task, login_suggest_task, long_job_task, celery_scan_nets_with_fping, \
    celery_discover_vendor, celery_get_config, celery_cmd_runner
from net.models import Job, JobResult, Scripts, Equipment
from argus.models import ASTU
import subprocess
from pygments.lexer import RegexLexer, bygroups
from pygments.token import *
from pygments import highlight
from pygments.formatters import HtmlFormatter
import mistune


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

    job = Job()
    job.script = Scripts.objects.get(id=script_id)

    # We need to run celery task with some countdown.
    COUNTDOWN = 3.0

    if script_id == '1':
        # ping
        # task = ping_task.delay(destinations_ids)
        task = ping_task.apply_async((destinations_ids,), track_started=True, countdown=COUNTDOWN)
    elif script_id == '2':
        # task = long_job_task.delay()
        task = long_job_task.apply_async(track_started=True, countdown=COUNTDOWN)
    elif script_id == '3':
        # task = login_suggest_task.delay(destinations_ids)
        task = login_suggest_task.apply_async((destinations_ids,), track_started=True, countdown=COUNTDOWN)
    elif script_id == '999':
        # task = celery_scan_nets_with_fping.delay(subnets=destinations_ids)
        task = celery_scan_nets_with_fping.apply_async(kwargs={'subnets': destinations_ids}, track_started=True,
                                                       countdown=COUNTDOWN)
        destinations_ids = list()
    elif script_id == '1000':
        # task = celery_discover_vendor.delay(subnets=destinations_ids)
        task = celery_discover_vendor.apply_async(kwargs={'subnets': destinations_ids}, track_started=True,
                                                  countdown=COUNTDOWN)
        destinations_ids = list()
    elif script_id == '1001':
        # task = celery_discover_vendor.delay(subnets=destinations_ids)
        task = celery_get_config.apply_async(kwargs={'subnets': destinations_ids}, track_started=True,
                                             countdown=COUNTDOWN)
        destinations_ids = list()
    else:
        return False

    job.celery_id = task.task_id
    job.status = 'PENDING'
    job.save()

    # Adding NE id's to Job table, so we can put NE's to template
    for ne in destinations_ids:
        job.ne_ids.add(ASTU.objects.get(pk=ne))
        job.save()
    pass


def scan_nets_with_fping(subnets):
    found, new = 0, 0  # Found Alive IP's and created ones
    for subnet in subnets:
        proc = subprocess.Popen(["/usr/bin/sudo /sbin/fping -O 160 -a -q -r 0 -i 1 -g %s" % subnet], shell=True,
                                stdout=subprocess.PIPE)
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
                    eq.get_config()
                eq.disconnect()
    return login_suggest_success_count, vendor_found_count


# thx for nocproject.org for lexers

class NOCCiscoLexer(RegexLexer):
    name = "Cisco.IOS"
    tokens = {
        "root": [
            (r"^!.*", Comment),
            (r"(description)(.*?)$", bygroups(Keyword, Comment)),
            (r"(password|shared-secret|secret)(\s+[57]\s+)(\S+)", bygroups(Keyword, Number, String.Double)),
            (r"(ca trustpoint\s+)(\S+)", bygroups(Keyword, String.Double)),
            (r"^(interface|controller|router \S+|voice translation-\S+|voice-port)(.*?)$", bygroups(Keyword, Name.Attribute)),
            (r"^(dial-peer\s+\S+\s+)(\S+)(.*?)$", bygroups(Keyword, Name.Attribute, Keyword)),
            (r"^(vlan\s+)(\d+)$", bygroups(Keyword, Name.Attribute)),
            (r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(/\d{1,2})?", Number),  # IPv4 Address/Prefix
            (r"49\.\d{4}\.\d{4}\.\d{4}\.\d{4}\.\d{2}", Number),  # NSAP
            (r"(\s+[0-9a-f]{4}\.[0-9a-f]{4}\.[0-9a-f]{4}\s+)", Number),  # MAC Address
            (r"^(?:no\s+)?\S+", Keyword),
            (r"\s+\d+\s+\d*|,\d+|-\d+", Number),
            (r".", Text),
        ],
    }


class NOCJuniperLexer(RegexLexer):
    name = "Juniper.JUNOS"
    tokens = {
        "root": [
            (r"#.*$", Comment),
            (r"//.*$", Comment),
            (r"/\*", Comment, "comment"),
            (r"\"", String.Double, "string"),
            (r"inactive:", Error),
            (r"(\S+\s+)(\S+\s+)({)", bygroups(Keyword, Name.Attribute, Punctuation)),
            (r"(\S+\s+)({)", bygroups(Keyword, Punctuation)),
            (r"https?://.*?[;]", String.Double),
            (r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(/\d{1,2})?", Number),  # IPv4 Address/Prefix
            (r"49\.\d{4}\.\d{4}\.\d{4}\.\d{4}\.\d{2}", Number),  # NSAP
            (r"[;\[\]/:<>*{}]", Punctuation),
            (r"\d+", Number),
            (r".", Text)
        ],
        "comment": [
            (r"[^/*]", Comment),
            (r"/\*", Comment, "#push"),
            (r"\*/", Comment, "#pop"),
            (r"[*/]", Comment)
        ],
        "string": [
            (r".*\"", String.Double, "#pop")
        ]
    }


class NOCHuaweiLexer(RegexLexer):
    name = "Huawei.VRP"
    tokens = {
        "root": [
            (r"^#.*", Comment),
            (r"(description)(.*?)$", bygroups(Keyword, Comment)),
            (r"^(interface|ospf|bgp|isis|acl name)(.*?)$", bygroups(Keyword, Name.Attribute)),
            (r"^(vlan\s+)(\d+)$", bygroups(Keyword, Name.Attribute)),
            (r"^(vlan\s+)(\d+\s+)(to\s+)(\d+)$", bygroups(Keyword, Name.Attribute, Keyword, Name.Attribute)),
            (r"^(?:undo\s+)?\S+", Keyword),
            (r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(/\d{1,2})?", Number),  # IPv4 Address/Prefix
            (r"49\.\d{4}\.\d{4}\.\d{4}\.\d{4}\.\d{2}", Number),  # NSAP
            (r"\d+", Number),
            (r".", Text)
        ]
    }


class HighlightRenderer(mistune.Renderer):
    def __init__(self, vendor=None):
        super().__init__()
        self.vendor = vendor

    def block_code(self, code, lang):
        if self.vendor == 'Cisco':
            lexer = NOCCiscoLexer()
        elif self.vendor == 'Juniper':
            lexer = NOCJuniperLexer()
        elif self.vendor == 'Huawei':
            lexer = NOCHuaweiLexer()
        else:
            lexer = NOCCiscoLexer()
        formatter = HtmlFormatter()
        return highlight(code, lexer, formatter)


def cmd_to_celery(vendor, ips, cmds):
    task = celery_cmd_runner.apply_async(kwargs={'vendor': vendor, 'ips': ips, 'cmds': cmds})
    pass
