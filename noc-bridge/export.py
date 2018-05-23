import sys, os, django
from django.conf import settings
sys.path.append('/home/hu4/lna')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()
import csv
from net.models import Equipment
from argus.models import ASTU


def generate_noc_csv():
    all_equipment = Equipment.objects.filter(hostname__isnull=False)

    with open('noc-import.csv', 'w', newline='') as csvfile:
        fieldnames = ['name', 'is_managed', 'container', 'administrative_domain', 'segment', 'pool', 'profile',
                      'vendor', 'platform', 'version', 'next_version', 'object_profile', 'description', 'auth_profile',
                      'scheme', 'address', 'port', 'user', 'password', 'super_password', 'remote_path',
                      'trap_source_type', 'trap_source_ip', 'syslog_source_type', 'syslog_source_ip', 'trap_community',
                      'snmp_ro', 'snmp_rw', 'access_preference', 'vc_domain', 'vrf', 'controller', 'local_cpe_id',
                      'global_cpe_id', 'last_seen', 'termination_group', 'service_terminator', 'shape', 'time_pattern',
                      'config_filter_handler', 'config_diff_filter_handler', 'config_validation_handler', 'max_scripts',
                      'x', 'y', 'default_zoom', 'software_image', 'remote_system', 'remote_id', 'escalation_policy',
                      'box_discovery_alarm_policy', 'periodic_discovery_alarm_policy', 'box_discovery_telemetry_policy',
                      'box_discovery_telemetry_sample', 'periodic_discovery_telemetry_policy',
                      'periodic_discovery_telemetry_sample', 'tt_system', 'tt_queue', 'tt_system_id',
                      'cli_session_policy', 'cli_privilege_policy', 'autosegmentation_policy',
                      'event_processing_policy', 'tags']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        counter = 0

        for eq in all_equipment:
            rowdict = get_row_dict_from(eq)
            writer.writerow(rowdict=rowdict)
            counter += 1
            # if counter >=50:
            #     return True

        print(f"total {counter} in generated csv")


def get_row_dict_from(eq):
    row = {}
    actual_ip = str(eq.ne_ip).replace('/32', '')
    row['name'] = eq.hostname
    row['is_managed'] = 'True'
    row['administrative_domain'] = 'default'
    row['segment'] = 'ALL'
    row['pool'] = 'default'
    row['profile'] = get_sa_profile_from(eq)
    row['object_profile'] = get_object_profile_from(eq)
    row['description'] = get_description(actual_ip)
    row['auth_profile'] = 'all-suggest'
    row['scheme'] = 1
    row['address'] = actual_ip
    row['port'] = 0
    row['user'] = ''
    row['password'] = ''
    row['trap_source_type'] = 'a'
    row['syslog_source_type'] = 'a'
    row['trap_community'] = 'nocnbr'
    row['access_preference'] = 'P'
    row['shape'] = 'Cisco/workgroup_switch'
    row['max_scripts'] = 0
    row['escalation_policy'] = 'P'
    row['box_discovery_alarm_policy'] = 'P'
    row['periodic_discovery_alarm_policy'] = 'P'
    row['box_discovery_telemetry_policy'] = 'P'
    row['box_discovery_telemetry_sample'] = 0
    row['periodic_discovery_telemetry_policy'] = 'P'
    row['periodic_discovery_telemetry_sample'] = 0
    row['cli_session_policy'] = 'P'
    row['cli_privilege_policy'] = 'P'
    row['autosegmentation_policy'] = 'P'
    row['event_processing_policy'] = 'P'
    row['tags'] = get_tags_for(eq)

    return row

def get_sa_profile_from(eq):
    """
    Returns managed object SA profile from NOC
    :param eq:
    :return:
    """
    if eq.vendor == 'Alcatel':
        return 'Alcatel.7302'
    if eq.vendor == 'Cisco':
        return 'Cisco.IOS'
    if eq.vendor == 'Eltex':
        return 'Eltex.MES'
    if eq.vendor == 'Huawei':
        return 'Huawei.VRP'
    if eq.vendor == 'Huawei OLT':
        return 'Huawei.MA5600T'
    if eq.vendor == 'Juniper':
        return 'Juniper.JUNOS'
    if eq.vendor == 'SNR':
        return 'NAG.SNR'
    if eq.vendor == 'Zyxel':
        return 'Zyxel.DSLAM'  # Need to check
    print(f"Vendor / Profile not found for {eq.vendor}")
    return None

def get_object_profile_from(eq):
    """
    Returns managed object profile
    :param eq:
    :return:
    """

    router_model_list = ['Cisco 7206VXR', 'cisco ASR1001', 'Cisco C10008', 'mx480', 'mx80-p']

    if eq.model in router_model_list:
        return 'generic_router'
    return 'generic_switch'

def get_description(ip):
    """
    Location from ASTU
    :param ip:
    :return:
    """
    actual_ip = str(ip)
    try:
        astu_obj = ASTU.objects.get(ne_ip=actual_ip)
    except ASTU.DoesNotExist:
        return ''
    return astu_obj.address

def get_tags_for(eq):
    """
    Returns various tags for MO from EQ specifics
    :param eq:
    :return:
    """
    tags = eq.vendor.replace(' ', '')  # without spaces
    try:
        if len(eq.model) < 18:
            tags += ',' + eq.vendor
    except TypeError:  # model can be None
        pass

    # try:
    #     astu_obj = ASTU.objects.get(ne_ip=eq.ne_ip)
    # except ASTU.DoesNotExist:
    #     return tags
    #
    # tags += ',' + astu_obj.segment

    return tags


if __name__ == '__main__':
    generate_noc_csv()
