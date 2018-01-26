import time
import json
import logging
import subprocess
from celery import current_task, shared_task, states
from celery.exceptions import TaskRevokedError, WorkerShutdown, WorkerTerminate
from channels import Group
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.db.models import Q
from lna.taskapp.celery_app import app
from net.equipment.generic import b2a, GenericEquipment
from argus.models import ASTU
from net.models import Job, JobResult, Equipment, Subnets
import concurrent.futures
import multiprocessing
from django.db import connection
from transliterate import translit


# MAX_WORKERS = multiprocessing.cpu_count()*40
MAX_WORKERS = 40

log = logging.getLogger(__name__)


def update_job_status(app_task, state=None, meta=None, result=None, message=None):
    celery_id = app_task.request.id
    job, is_created = Job.objects.get_or_create(celery_id=celery_id)
    if is_created:
        log.warning('update_job_status: Job object was created in job itself, not in django!')
        job.name = app_task.name
        job.script_id = 777  # Crontab or direct called script
    app_task.update_state(state=state, meta=meta)

    if state:
        job.status = state
        if state == 'SUCCESS':
            job.completed = timezone.now()

    # if meta arg is exists, we put in db and later send job/task status update
    if meta:
        job.meta = meta
    else:
        # assuming that work is completed
        meta = {'current': 100, 'total': 100, }
        job.meta = meta

    job.save()
    if result:
        job_result, created = JobResult.objects.get_or_create(job_id=job)
        job_result.result += result  # adding result
        job_result.save()
    Group("task_watcher_%s" % str(job.id)).send(
        {"text": json.dumps({
            "script_name": job.script.name,
            "meta": {
                "current": meta['current'],
                "total": meta['total'],
            },
            "result": result,
            'result_update': message
        })}
    )
    pass


def scan_nets_with_fping_task_version(subnets):
    # test to avoid double import
    found, new = 0, 0  # Found Alive IP's and created ones
    for subnet in subnets:
        proc = subprocess.Popen(["/usr/bin/sudo /sbin/fping -O 160 -i 1 -a -q -r 0 -g %s" % subnet], shell=True,
                                stdout=subprocess.PIPE)
        proc.wait()
        out = proc.stdout.read()
        alive_list = out.decode().split('\n')[:-1]  # everything but the last empty
        log.debug("alive list is:")
        log.debug(alive_list)
        for ip in alive_list:
            log.info("Trying to get or create object with IP = %s" % ip)
            obj, created = Equipment.objects.get_or_create(ne_ip=ip.split(' ')[0])
            found += 1
            if created:
                new += 1
                obj.hostname = None
                obj.vendor = None
                obj.model = None
                obj.save()
                log.info("object with IP = %s created and saved" % ip)
            else:
                log.info("object with IP = %s exists, can't create it again" % ip)
            # return found, new
    return found, new


@shared_task(time_limit=10*60)
def long_job(job_id, reply_channel):
    for i in range(3):
        log.info("Tick " + str(i))
        print("Tick " + str(i))
        time.sleep(3)

    pass


@shared_task(time_limit=10*60)
def check_online():
    """
    Checking NE status with FPING
    :return:
    """
    ne_objects = ASTU.objects.all().filter(status='эксплуатация')
    fping_ips_str = ''  # ip addresses separated by space for fping
    for ne in ne_objects:
        fping_ips_str += str(ne.ne_ip) + " "
    #  Type of service = 160, only alive, quiet, zero repeat
    proc = subprocess.Popen(["/usr/bin/sudo /sbin/fping -O 160 -i 1 -a -q -r 0 %s" % fping_ips_str], shell=True, stdout=subprocess.PIPE)
    proc.wait()
    out = proc.stdout.read()
    alive_list = out.decode().split('\n')[:-1]  # everything but the last empty
    ASTU.objects.all().update(is_online=False)
    for alive_ip in alive_list:
        obj = ASTU.objects.get(ne_ip=alive_ip)
        obj.is_online = True
        obj.save()
    return {'status': 'Completed', 'alive_objects': len(alive_list)}


def get_destination_ips_list(destination_ids):
    """
    Function to get IP addresses from NE id's list.
    :param destination_ids: ['100', '200', ...]
    :return: ['10.205.18.1', 10.205.18.2', ...]
    """
    return [ASTU.objects.get(pk=ne_id).ne_ip for ne_id in destination_ids]  # list of IPs


@app.task(bind=True, time_limit=10*60)
def login_suggest_task(self, destination_ids):
    log.info('celery task in login_suggest.py')
    total = len(destination_ids)
    update_job_status(self, state=states.STARTED, meta={'current': 0, 'total': total},
                      message='Login Suggest task was started')
    i = 1  # counter for updating progress
    task_result = ""  # After-all result of discovering credentials
    for target_id in destination_ids:  # getting ID
        try:
            astu_object = ASTU.objects.get(pk=target_id)  # getting ASTU object
            # Getting or creating Equipment object with IP-address of ASTU object
            eq_obj, created = Equipment.objects.get_or_create(ne_ip=astu_object.ne_ip)
            eq = GenericEquipment(eq_obj, inside_celery=True)
            result = eq.suggest_login(resuggest=False)  # dict
            if result:
                result_to_send = "<br>[%s]Discovered credentials, L: %s, P: %s" % \
                                 (result['ip'], result['login'], result['password'])
                task_result += "<br>[%s]Discovered credentials, L: %s, P: %s" % \
                               (result['ip'], result['login'], result['password'])
            else:
                result_to_send = "<br>Failed to discover credentials for %s" % (astu_object.ne_ip, )
                task_result += "<br>Failed to discover credentials for %s" % (astu_object.ne_ip, )
            update_job_status(self, state=states.STARTED, meta={'current': i, 'total': total},
                              message=result_to_send)
            i += 1
        except TaskRevokedError:
            log.error("TASK WAS REVOKED!")
            break
        except WorkerShutdown:
            log.error("WORKER WAS Shutdowned!")
            break
        except WorkerTerminate:
            log.error("WORKER WAS Terminated!")
            break
    update_job_status(self, state=states.SUCCESS, result=task_result, message='DONE!')
    return task_result


@app.task(bind=True, time_limit=10*60)
def ping_task(self, destination_ids, **kwargs):
    log.warning("celery task in ping.py ")
    update_job_status(self, state=states.STARTED, meta={'current': 0, 'total': len(destination_ids)},
                      message='ping task was started')
    targets = get_destination_ips_list(destination_ids)
    targets = " ".join(targets)  # string with space separated IPs
    proc = subprocess.Popen(["/usr/bin/sudo /sbin/fping %s" % targets], shell=True, stdout=subprocess.PIPE)
    proc.wait()
    out = b2a(proc.stdout.read())  # convert from binary to ascii
    out = out.replace("\n", "<br>\n")  # some html breaks
    update_job_status(self, state=states.SUCCESS, result=out, message='DONE!')


@app.task(bind=True, time_limit=10*60)
def long_job_task(self, *args, **kwargs):
    RANGE = 60  # how long it will be runs
    for i in range(RANGE):
        time.sleep(1)
        log.debug('Tick %s of %s' % (str(i), str(RANGE)))
        message_to_user = "current: %s, total: %s" % (str(i), str(RANGE))
        update_job_status(self, state=states.STARTED, meta={'current': i, 'total': RANGE}, message=message_to_user)
    # meta is JSON field, it cant' be empty
    update_job_status(self, state=states.SUCCESS, result='My Mega Long Result', message='DONE!')
    return {"status": "Long Task completed", "num_of_seconds": RANGE}


@app.task(bind=True, time_limit=40*60)
def celery_scan_nets_with_fping(self, subnets=('',)):
    """
    Task for scan subnets with fping

    :param self: Celery task reference

    :param subnets: list (or tuple, or iterable) with subnets, eg ['10.205.0.0/24', '10.205.1.0/24', ...]

    :return: None
    """
    log.warning("celery task in celery_scan_nets_with_fping")
    # task called without arguments | tuple or list or None
    if subnets == ('', ) or subnets == ['', ] or subnets is None:
        subnets_objects = Subnets.objects.all()
        log.info('Task called without parameters, getting subnets from DB')
        subnets = [s.network for s in subnets_objects]

    update_job_status(self, state=states.STARTED, meta={'current': 0, 'total': len(subnets)},
                      message='ping task was started')
    found, new, subnet_counter, result = 0, 0, 0, ''  # counters of alive hosts and loop below counter
    for subnet in subnets:
        current_found, current_new = scan_nets_with_fping_task_version(list((subnet, )))
        # we send only one subnet to func,
        # so we can update task status
        # Everything actually work makes 'scan_nets_with_fping', it will be found alive hosts and put new hosts to DB
        # So we need only to update task status:
        subnet_counter += 1
        found += current_found
        new += current_new
        result += "<br>\n" + 'Scan of %s result: %s alive, %s new hosts' % (subnet, current_found, current_new)
        update_job_status(self, state=states.STARTED,
                          meta={'current': subnet_counter, 'total': len(subnets)},
                          message='Scan of %s result: %s alive, %s new hosts' % (subnet, current_found, current_new))
    # After loop end:
    update_job_status(self, state=states.SUCCESS, result=result)


def discover_one_host(host):
    """
    Does network element discovery for one hosts. Returns message with discovery result.

    :param host: Equipment object

    :return: string, message with discovery result
    """
    eq = GenericEquipment(host, inside_celery=True)
    message_from_celery = "Host: %s." % eq.ip
    # need to adjust it? or 1 sec is enough?
    eq.set_io_timeout(1)
    login_suggest_status = eq.suggest_login(resuggest=False)
    eq.disconnect()
    if login_suggest_status:
        message_from_celery += " Login suggestion was successful."
        # Trying to login only if login guessing was successful
        if eq.connect():
            eq.do_login()
            vendor = eq.discover_vendor()
            if vendor:
                message_from_celery += " Vendor was found: %s" % vendor
                # config discovery is too slow
                # eq.get_config()
            eq.disconnect()
    connection.close()  # close django db connection for thread
    return message_from_celery


def get_config_from(host):
    """
    Does config discovery for one host. Returns message with result

    :param host: Equipment object

    :return: string, message with discovery result
    """
    message_from_celery = "Host: %s." % host
    try:
        eq = GenericEquipment(host, inside_celery=True)
        eq.set_io_timeout(1)
        if not eq.connect():
            return message_from_celery + " Can not connect."
        eq.do_login()
        if eq.get_config():
            message_from_celery += " Config fetched successfully"
        else:
            message_from_celery += " Can't get config from NE"
        eq.disconnect()
    except Exception as e:
        message_from_celery += 'exception: ' + e.args

    connection.close()  # close django db connection for thread anyway
    return message_from_celery


@app.task(bind=True, time_limit=60*60)
def celery_discover_vendor(self, subnets=('',)):
    """
    Does network element discovery and finds logins/passwords from credentials database. Works in Celery

    :param subnets: list with subnets to discover

    :param self: Celery task reference

    :return: None

    """

    # task called without arguments | tuple or list or None
    if subnets == ('',) or subnets == ['', ] or subnets is None:
        subnets_objects = Subnets.objects.all()
        log.info('Task called without parameters, getting subnets from DB')
        subnets = [s.network for s in subnets_objects]

    login_suggest_success_count = 0
    vendor_found_count = 0
    log.warning("Celery task in celery_discover_vendor")
    log.info("Subnets are: %s" % subnets)
    result = ""  # Task result

    # First, we need to count NE total
    total, host_counter = 0, 0  # total host to discover, completed host counter

    for subnet in subnets:
        # If we can't find "/" (slash) symbol in subnets, than user had entered the host only, and no subnet
        # log.info('Got subnet %s' % subnet)
        try:
            if subnet.find("/") == -1:
                # one host
                hosts = Equipment.objects.get(ne_ip=subnet)
                total += 1  # assuming that IP address is unique field in DB
                log.info("Got one host: %s" % hosts.ne_ip)
            else:
                log.info('Subnet slash "/" found in %s' % subnet)
                hosts = Equipment.objects.filter(ne_ip__net_contained=subnet)
                count = hosts.count()
                total += count
                log.info("Got subnet %s with %s hosts" % (subnet, count))
        except AttributeError:  # exception in case subnet was taken from DB
            # subnet
            hosts = Equipment.objects.filter(ne_ip__net_contained=subnet)
            count = hosts.count()
            total += count
            log.info("Got subnet %s with %s hosts" % (subnet, count))

    result += "Discover vendor task has started. Total %s devices<br />\n" % total
    log.warning("Total host to scan: %s" % total)
    update_job_status(self, state=states.STARTED, meta={'current': 0, 'total': total},
                      message=result)

    for subnet in subnets:
        # If we can't find "/" (slash) symbol in subnets, than user had entered the host only, and no subnet
        try:
            if subnet.find("/") == -1:
                # one host
                hosts = Equipment.objects.filter(ne_ip=subnet)
            else:
                hosts = Equipment.objects.filter(ne_ip__net_contained=subnet)
        except AttributeError:
            # subnet
            hosts = Equipment.objects.filter(ne_ip__net_contained=subnet)

        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # start host discovery
            future_to_scan = {executor.submit(discover_one_host, host): host for host in hosts}
            # waiting for futures
            for future in concurrent.futures.as_completed(future_to_scan):
                future_result = future_to_scan[future]
                try:
                    message = future.result()
                    result += message + "<br />\n"
                    host_counter += 1
                    update_job_status(self, state=states.STARTED,
                                      meta={'current': host_counter, 'total': total}, message=message)
                except Exception as exc:
                    host_counter += 1
                    message = '%r generated an exception: %s' % (future_result, exc)
                    result += message + "<br />\n"
                    log.warning(message)
                    update_job_status(self, state=states.STARTED,
                                      meta={'current': host_counter, 'total': total}, message=message)
                else:
                    log.info(message)

    update_job_status(self, state=states.SUCCESS, result=result + '<br />Done.')
    return result


@app.task(bind=True, time_limit=60*60)
def celery_get_config(self, subnets=('',)):
    """
    Does config discovery. Works in Celery. Does only fast devices config fetch.

    :param subnets: list with subnets to discover

    :param self: Celery task reference

    :return: None

    """

    # task called without arguments | tuple or list or None
    if subnets == ('',) or subnets == ['', ] or subnets is None:
        subnets_objects = Subnets.objects.all()
        log.info('celery_get_config task called without parameters, getting subnets from DB')
        subnets = [s.network for s in subnets_objects]

    log.warning("Celery task in celery_get_config")
    log.info("Subnets are: %s" % subnets)
    result = ""  # Task result

    # First, we need to count NE total
    total, host_counter = 0, 0  # total host to discover, completed host counter

    for subnet in subnets:
        # If we can't find "/" (slash) symbol in subnets, than user had entered the host only, and no subnet
        # log.info('Got subnet %s' % subnet)
        try:
            if subnet.find("/") == -1:
                # one host
                hosts = Equipment.objects.get(ne_ip=subnet)
                total += 1  # assuming that IP address is unique field in DB
                log.info("Got one host: %s" % hosts.ne_ip)
            else:
                log.info('Subnet slash "/" found in %s' % subnet)
                hosts = Equipment.objects.filter(ne_ip__net_contained=subnet).filter(~Q(vendor='Alcatel')).\
                    filter(vendor__isnull=False).filter(telnet_port_open=True)
                count = hosts.count()
                total += count
                log.info("Got subnet %s with %s hosts" % (subnet, count))
        except AttributeError:  # exception in case subnet was taken from DB
            # subnet
            hosts = Equipment.objects.filter(ne_ip__net_contained=subnet).filter(~Q(vendor='Alcatel')).\
                filter(vendor__isnull=False).filter(telnet_port_open=True)
            count = hosts.count()
            total += count
            log.info("Got subnet %s with %s hosts" % (subnet, count))

    result += "Config discovery task has started. Total %s devices<br />\n" % total
    log.warning("Total host to scan: %s" % total)
    update_job_status(self, state=states.STARTED, meta={'current': 0, 'total': total},
                      message=result)

    for subnet in subnets:
        # If we can't find "/" (slash) symbol in subnets, than user had entered the host only, and no subnet
        try:
            if subnet.find("/") == -1:
                # one host
                hosts = Equipment.objects.filter(ne_ip=subnet)
            else:
                hosts = Equipment.objects.filter(ne_ip__net_contained=subnet).filter(~Q(vendor='Alcatel')).\
                    filter(vendor__isnull=False).filter(telnet_port_open=True)
        except AttributeError:
            # subnet
            hosts = Equipment.objects.filter(ne_ip__net_contained=subnet).filter(~Q(vendor='Alcatel')).\
                    filter(vendor__isnull=False).filter(telnet_port_open=True)

        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # start host discovery
            future_to_scan = {executor.submit(get_config_from, host): host for host in hosts}
            # waiting for futures
            for future in concurrent.futures.as_completed(future_to_scan):
                future_result = future_to_scan[future]
                try:
                    message = future.result()
                    result += message + "<br />\n"
                    host_counter += 1
                    update_job_status(self, state=states.STARTED,
                                      meta={'current': host_counter, 'total': total}, message=message)
                except Exception as exc:
                    host_counter += 1
                    message = '%r generated an exception: %s' % (future_result, exc)
                    result += message + "<br />\n"
                    log.warning(message)
                    update_job_status(self, state=states.STARTED,
                                      meta={'current': host_counter, 'total': total}, message=message)
                else:
                    log.info(message)

    update_job_status(self, state=states.SUCCESS, result=result + '<br />Done.')
    return result


def exec_commands_on_host(eq, cmds):
    result = list()
    eq.do_login()
    for cmd in cmds:
        output = eq.exec_cmd(cmd)
        result.append({'ip': eq.ip, 'command': cmd, 'result': output})
    eq.disconnect()
    return result


@app.task(bind=True, time_limit=60*60)
def celery_cmd_runner(self, **kwargs):
    # first if exact ip's list is given
    vendor = kwargs['vendor']
    cmds = kwargs['cmds'].splitlines()
    result = list()
    if kwargs['ips']:
        log.info("Running cmd runner with IP's list")
        ips_list = kwargs['ips'].splitlines()
        """
        for ip in ips_list:
            try:
                eq = GenericEquipment(Equipment.objects.get(ne_ip=ip), inside_celery=True)
                # check if vendor is correct
                if eq.equipment_object.vendor != vendor:
                    log.error("Wrong vendor! %s is %s, not %s" % (ip, eq.equipment_object.vendor, vendor))
                    continue
                result.append(exec_commands_on_host(eq, cmds))
            except Equipment.DoesNotExist:
                log.error("Equipment with IP=%s doesn't exists!" % ip)
        """
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures_to_exec_cmds = list()
            for ip in ips_list:
                try:
                    eq = GenericEquipment(Equipment.objects.get(ne_ip=ip), inside_celery=True)
                    # check if vendor is correct
                    if eq.equipment_object.vendor != vendor:
                        log.error("Wrong vendor! %s is %s, not %s" % (ip, eq.equipment_object.vendor, vendor))
                        continue  # next IP
                    if not eq.equipment_object.telnet_port_open:
                        log.error("Telnet port was closed at last discovery at %s!" % ip)
                        continue
                    futures_to_exec_cmds.append(executor.submit(exec_commands_on_host, eq, cmds))  # submit task
                except Equipment.DoesNotExist:
                    log.error("Equipment with IP=%s doesn't exists!" % ip)

            for future in concurrent.futures.as_completed(futures_to_exec_cmds):
                try:
                    result.append(future.result())
                except Exception as exc:
                    log.warning('it was an exception: %s' % exc)
            return result
    else:
        log.info("There were no IP in list, trying to get all NE with specific vendor")
        equipment_objects_by_vendor = Equipment.objects.all().filter(vendor=vendor).filter(telnet_port_open=True)
        log.info("Total %s NE's" % equipment_objects_by_vendor.count())
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures_to_exec_cmds = list()
            for obj in equipment_objects_by_vendor:
                eq = GenericEquipment(obj, inside_celery=True)
                futures_to_exec_cmds.append(executor.submit(exec_commands_on_host, eq, cmds))  # submit task
            for future in concurrent.futures.as_completed(futures_to_exec_cmds):
                try:
                    result.append(future.result())
                except Exception as exc:
                    log.warning('it was an exception: %s' % exc)
            return


def put_syslocation(eq, translit_location):
    """
    Calls put_syslocation from Equipment class
    :param eq: GenericEquipment object
    :param translit_location: Location to put in config
    :return:
    """
    eq.do_login()
    eq.put_syslocation(translit_location)
    eq.disconnect()


@app.task(bind=True, time_limit=60*60)
def celery_put_syslocation(self,  subnets=('',)):
    print(subnets)
    if subnets == ('',) or subnets == ['', ] or subnets is None:
        log.error('Subnets list can not be empty')
        return False

    result = list()
    hosts = list()

    for subnet in subnets:
        # If we can't find "/" (slash) symbol in subnets, than user had entered the host only, and no subnet
        log.warning('GOT SUBNET: %s' % subnet)
        try:
            if subnet.find("/") == -1:
                # one host
                hosts = Equipment.objects.filter(ne_ip=subnet).filter(telnet_port_open=True)
            else:
                hosts = Equipment.objects.filter(ne_ip__net_contained=subnet).filter(telnet_port_open=True)
        except AttributeError:
            # subnet
            hosts = Equipment.objects.filter(ne_ip__net_contained=subnet).filter(telnet_port_open=True)

        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures_to_exec_cmds = list()

            for host in hosts:
                ip = str(host.ne_ip)
                try:
                    astu = ASTU.objects.get(ne_ip=ip)
                    location = astu.address
                    translit_location = translit(location, 'ru', reversed=True)

                    # Replacing some characters
                    # translit_location = translit_location.replace(' ', '_')
                    # translit_location = translit_location.replace('(', '')
                    # translit_location = translit_location.replace(')', '')
                    # translit_location = translit_location.replace('.', '_')
                    translit_location = translit_location.replace('«', '')
                    translit_location = translit_location.replace('»', '')
                    translit_location = translit_location.replace("'", '')
                    translit_location = translit_location.replace('"', "'")
                    translit_location = translit_location.replace("“", '')
                    translit_location = translit_location.replace("”", '')
                    translit_location = translit_location.replace("№", 'N')
                    log.debug("%s at %s" % (ip, translit_location))

                    eq = GenericEquipment(host, inside_celery=True)

                    futures_to_exec_cmds.append(executor.submit(put_syslocation, eq, translit_location))  # submit task

                except ASTU.DoesNotExist:
                    log.warning("host with IP %s not found in ASTU" % ip)

            for future in concurrent.futures.as_completed(futures_to_exec_cmds):
                try:
                    result.append(future.result())
                except Exception as exc:
                    log.warning('it was an exception: %s' % exc)

    return result

