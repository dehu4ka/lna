from net.models import Equipment, Credentials, EquipmentSuggestCredentials, EquipmentConfig
from telnetlib import Telnet
import logging
import re
import socket
from net.equipment.exceptions import NoLoginPrompt, NoPasswordPrompt, NoKnownPassword, NotLoggedIn, BadCommandPrompt, \
    NotConnected
from time import sleep
from net.libs.colors import Colors
from argus.models import ASTU

c = Colors()

handler = logging.StreamHandler()


def a2b(ascii_str):  # ascii to binary
    return ascii_str.encode('ascii')


def b2a(bin_string):  # binary to ascii
    return bin_string.decode('ascii', 'replace')


LOGIN_PROMPTS = [
    re.compile(b'username: ', flags=re.I),
    re.compile(b'username:', flags=re.I),
    re.compile(b'login: ', flags=re.I),
    re.compile(b'login:', flags=re.I),
    re.compile(b'user name:', flags=re.I),
    re.compile(b'user name: ', flags=re.I),
    re.compile(b'>>User name:', flags=re.I),

]

PASSWORD_PROMPTS = [
    re.compile(b'pass: ', flags=re.I),
    re.compile(b'pass:', flags=re.I),
    re.compile(b'password: ', flags=re.I),
    re.compile(b'password:', flags=re.I),
    re.compile(b'>>User password:', flags=re.I),
]

AUTHENTICATION_FAILED = [
    re.compile(b'Authentication failed', flags=re.I),  # cisco
    re.compile(b'Password incorrect', flags=re.I),  # cisco
    re.compile(b'Login incorrect', flags=re.I),  # juniper
    re.compile(b'Bad Password', flags=re.I),  # zyxel
    re.compile(b'Error: Failed to authenticate', flags=re.I),  # huawei no tacacs
    re.compile(b'Error: Password incorrect', flags=re.I),  # huawei
    re.compile(b'Invalid user name and password', flags=re.I),  # SNR
    re.compile(b'Username or password invalid.', flags=re.I),  # Huawei OLT
]


def setup_logger(name, verbosity=1):
    """
    Basic logger
    """
    # formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
    # formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    formatter = logging.Formatter(fmt='%(message)s')  # looks very very better for telnet sessions
    handler.setFormatter(formatter)

    # Set up main logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    if verbosity > 1:
        logger.setLevel(logging.DEBUG)

    return logger


class GenericEquipment(object):
    def __init__(self, equipment_object, inside_celery=False):
        if not isinstance(equipment_object, Equipment):
            raise Exception("Passed to constructor not Equipment Object")
        self.equipment_object = equipment_object
        # ne_ip is ipaddress.ip_interface, see https://docs.python.org/3/library/ipaddress.html
        self.ip = str(equipment_object.ne_ip.ip)
        self.l = setup_logger('net.equipment.generic', 2)  # 2 means debug
        self.l.debug('Equipment object was created, IP: %s', self.ip)
        self.t = Telnet()
        self.is_connected = False  # telnet connection status
        self.prompt = ''  # приглашение командной строки
        self.pager = self.init_pager()
        self.is_logged = False  # authorization status
        self.in_configure_mode = False
        self.io_timeout = 1  # timeout between entering CMD and waiting for output
        self.inside_celery = inside_celery  # is code runs inside Celery
        if equipment_object.credentials:
            self.username = equipment_object.credentials.login
            self.passw = equipment_object.credentials.passw
        else:
            self.username = None
            self.passw = None

    def _sleep(self, timeout=1.0):
        self.l.debug("Sleeping for " + str(timeout) + " sec")
        sleep(timeout)

    def set_io_timeout(self, io_timeout):
        """
        Sets input output timeout global to object
        :param io_timeout:
        :return:
        """
        self.io_timeout = io_timeout

    @staticmethod
    def init_pager():
        #  Заполняем возможные значения пэйджеров, на выходе получается список. Будет заполняться позднее, исходя из
        #  того что выдаст зоопарка оборудования
        pagers = list()
        pagers.append(re.compile(b'---\(more\)---'))
        pagers.append(re.compile(b'---\(more.+\)---'))
        pagers.append(re.compile(b' --More-- '))
        pagers.append(re.compile(b'  ---- More ----'))
        pagers.append(re.compile(b'All: a, More: <space>, One line: <return>, Quit: q or <ctrl>\+z'))
        pagers.append(re.compile(b"press 'e' to exit showall, 'n' for nopause, or any key to continue\.\.\."))
        pagers.append(re.compile(b"---- More \( Press 'Q' to break \) ----"))
        # pagers.append(re.compile(b'return user view with Ctrl\+Z'))
        return pagers

    def __del__(self):
        self.disconnect()

    def connect(self):
        """
        Tries to connect
        :return:
        True if success
        False if fail
        """
        self.is_connected = False  # by default
        try:
            self.t.open(self.ip, 23, self.io_timeout)
        except ConnectionRefusedError:
            self.l.warning("Connection to %s is refused!", self.ip)
        except socket.timeout:
            self.l.warning("Connection to %s - timeout!", self.ip)
        except OSError:
            self.l.info("OS Error, probably host have some firewall turned on, firewall is sending ICMP reject"
                        "and OS Error exception raised.")
        else:
            self.l.debug('Connection to %s was successful', self.ip)
            self.is_connected = True
        finally:
            if self.is_connected:
                if not self.equipment_object.telnet_port_open:  # if in DB port is closed,
                    self.equipment_object.telnet_port_open = True  # then set it open
                    self.equipment_object.save()  # and write changes
                return True
            else:  # when we can not connect for some reason
                if self.equipment_object.telnet_port_open:  # if in DB port is open,
                    self.equipment_object.telnet_port_open = False  # then set it closed
                    self.equipment_object.save()  # and write changes
                return False

    def disconnect(self):
        self.is_connected = False  # pointless ?
        self.is_logged = False
        self.t.close()

    def suggest_login(self, resuggest=False):
        """Tries to guess or suggest in other words device's login and password. Uses credentials stored in credentials database.

        :param resuggest: If we already have credentials in the DB and still want to try new suggestions

        :return: Dict with IP, Login, Pass if suggestion was successful or False if we can't suggest login/pass
        """
        if resuggest is False and self.equipment_object.credentials:
            self.l.info('Credentials are already in the DB')
            return {
                        'ip': self.ip,
                        'login': self.username,
                        'password': self.passw
                    }
        # Trying to connect before login attempts
        if not self.connect():
            self.l.info("Cannot connect! Telnet port is closed or other error. We shouldn't try to suggest login for "
                        "that type of NE")
            return False

        credentials = Credentials.objects.all()  # every login/password pairs
        for credential in credentials:
            # if it was tested, length of this filter will be 0
            was_it_tested = len(EquipmentSuggestCredentials.objects.filter(credentials_id=credential.id,
                                                                           equipment_id=self.equipment_object.id))
            if was_it_tested != 0:
                self.l.debug("Credentials was tested earlier: %s / %s", credential.login, credential.passw)
                self.l.debug("Skipping this...")
                continue  # skipping this one
            # Trying to login with that creds:
            self.l.info("SUGGESTING LOGIN | Trying to login with L: %s, P: %s to device: %s" %
                        (c.YELLOW + credential.login + c.RESET, c.PURPLE + credential.passw + c.RESET,
                         c.RED + self.ip + c.RESET))
            self.username = credential.login
            self.passw = credential.passw
            if not self.is_connected:
                if not self.connect():  # connecting
                    self.l.warning("Can't connect, so we can't suggest login.")
                    self.disconnect()
                    return False
            try:
                if self.try_to_login():  # if login was successful
                    self.l.info('Credentials for %s discovered! L: %s, P: %s', self.ip, self.username, self.passw)
                    self.equipment_object.credentials = credential  # going to write that to DB
                    self.equipment_object.save()
                    self.disconnect()  # Disconnecting for to be sure about connect/disconnect status
                    # return True
                    return {
                        'ip': self.ip,
                        'login': self.username,
                        'password': self.passw
                    }
                else:  # In case of Authentication failed
                    # do not care about results
                    tested, created = EquipmentSuggestCredentials.\
                        objects.get_or_create(equipment_id=self.equipment_object, credentials_id=credential)
                    tested.was_checked = True
                    tested.save()
                    self.l.debug("Created EquipmentSuggestCredentials with was_checked = True for equipment_id=%s,"
                                 " credentials_id=%s ",
                                 self.equipment_object.id, credential.id)
            except EOFError:
                self.l.info("Disconnected suddenly")
                # Unfortunately we can't be sure if disconnect were caused by invalid login or by other circumstances
                self.disconnect()
            except ConnectionResetError:
                self.l.info("Connection reset error.")
                self.disconnect()
                return False  # Other connection attempts will be unsuccessful, Alcatel anti-bruteforce.
            except NoPasswordPrompt:
                self.l.info("Disconnecting. No Password Prompt were detected at %s" % self.ip)
                self.disconnect()
            except NoLoginPrompt:
                self.l.info("Disconnecting. No Login Prompt were detected")
                self.disconnect()
        self.l.warning("%sCouldn't find suggested credentials at %s %s" % (c.CYAN + c.BOLD, self.ip, c.RESET))
        self.disconnect()  # Disconnecting
        # Pushing None values to self object login and password
        self.username = None
        self.passw = None
        self.l.debug("Deleting already checked credentials in hope that next login/password suggest "
                     "attempts will be successful")
        EquipmentSuggestCredentials.objects.filter(equipment_id=self.equipment_object.id).delete()
        return False

    def expect(self, re_list):
        """
        Expecting to find some of RE's in input re_list.

        :param re_list: List of compiled Regular Expressions

        :return: Returns tuple, first el - was any RE found or not, second - output in
        """
        str = self.t.expect(re_list, self.io_timeout)
        if str[0] == -1:
            self.l.debug("can't find expected string in string")
            # line below has very ugly output, so I have to comment it =)
            # self.l.debug("search was: %s", re_list)
            return False, b2a(str[2])  # not found
        self._print_recv(b2a(str[2]))
        # otherwise string is found, returning it ascii
        self.l.debug("Match object is %s" % str[1])  # prints match object for debugging purposes
        return True, b2a(str[2])
        # return str[2]

    def send(self, line):
        """
        Sends string with ENTER key and do some fancy debug output
        :param line: string to send to device
        :return: None
        """
        self.l.debug('>>>> sending')
        self.l.debug(c.RED + c.BOLD + line + c.RESET)
        self.t.write(a2b(line + "\n"))
        self.l.debug('>>>> sending end')

    def exec_cmd(self, cmd):
        """
        Executes command with ENTER key, returns command output
        :param cmd:
        :return:
        """
        if not self.is_logged:
            raise NotLoggedIn(self.ip)
        output = ''  # all output in ascii will be here
        self.l.debug('>>>> sending')
        self.l.debug(c.RED + c.BOLD + cmd + c.RESET)
        self.t.write(a2b(cmd + "\n"))
        self.l.debug('>>>> sending end')
        expect_list = self.pager
        re_with_prompt = re.compile(a2b(self.prompt))
        expect_list.append(re_with_prompt)  # If we have in our expect list both shell prompt and more prompt,
        #  we should not wait too long
        while True:
            out = self.t.expect(self.pager, timeout=self.io_timeout)
            output += b2a(out[2])
            if out[0] == -1:
                self.l.warning('Got IO Timeout on %s in exec_cmd(), cmd was: %s' % (self.ip, cmd))
                break
            if out[1].re != re_with_prompt:  # out[1] is re match object. out[1].re is matched regular expression
                self.l.debug('sending SPACE in exec_cmd()')
                self.t.write(a2b(' '))  # sending SPACE to get next page
            elif out[1].re == re_with_prompt:
                self.l.debug('Got prompt, command execution complete.')
                break
        self._print_recv(output)
        return output

    def _print_recv(self, input_string):
        """
        Prints received output to console with colors

        :param input_string: The string will be colored in debug output

        :return: None
        """
        # We are going to print that, so...
        if input_string is True:
            input_string = 'True'
        if input_string is False:
            input_string = 'False'
        self.l.debug('<<<< received')
        self.l.debug(c.BOLD + c.GREEN + input_string + c.RESET)
        self.l.debug('<<<< received end')

    def try_to_login(self):
        """
        Trying to login. First get some login prompt, pushing login, then get some password prompt.
        Use this def when you are unsure in loging and password

        :return: False if login attempt was unsuccessful, otherwise - True
        """
        self._sleep(0.5)
        self.l.debug("GenericEquipment.try_to_login method. \nExpecting login prompt:")
        was_found, out = self.expect(LOGIN_PROMPTS)
        # self._print_recv(out)
        if not was_found:  # we are expecting to see login prompt
            self.l.warning("Can't find login prompt at %s" % self.ip)
            raise NoLoginPrompt
        self.send(self.username)  # sending login
        self._sleep(1)
        self.l.debug("Expecting password prompt:")
        was_found, out = self.expect(PASSWORD_PROMPTS)
        # self._print_recv(out)
        if not was_found:  # same for password
            self.l.warning("Can't find password prompt at %s" % self.ip)
            raise NoPasswordPrompt
        self.send(self.passw)  # sending password
        self._sleep(5)  # 2 seconds because most equipment have big timeout after unsuccessful login
        self.l.debug("Expecting login or password prompt or auth failed in case of authentication is failed")
        was_found, out = self.expect(LOGIN_PROMPTS + PASSWORD_PROMPTS + AUTHENTICATION_FAILED)
        # self._print_recv(out)
        if was_found:  # if we are seeing login or password again - our creds are invalid
            self.l.warning('login "%s" and password "%s" for %s are invalid.', self.username, self.passw, self.ip)
            return False
        else:
            self.l.debug("Cant find login or password prompt in output. Generally it is a good sign.")
            self.l.debug("Output in binary form was: %s" % a2b(out))
        if out == '':
            self.l.warning("There was not output after login/password was sent. Probably bad password or dead AAA "
                           "servers, this leads to huge timeout. Try login to device manually.")
            self.disconnect()
            return False
        self.l.debug("Logged in with L: %s and P: %s", self.username, self.passw)
        return True

    def do_login(self):
        """
        Assuming that we are already know valid login and password from login_suggest. So, we need to login to device.
        Use this def when you are pretty sure in login and password.

        :return: True. Or Exception if something was wrong
        """
        if self.passw is None:
            raise NoKnownPassword
        if not self.connect():
            raise NotConnected(self.ip)
        # connecting
        was_found, out = self.expect(LOGIN_PROMPTS)  # we need to wait for login prompt
        self._print_recv(out)  # debug out
        self.send(self.username)  # sending known username
        was_found, out = self.expect(PASSWORD_PROMPTS)  # waiting for password prompt
        self._print_recv(out)  # debug out
        self.send(self.passw)  # sending known password
        self._sleep(0.5)  # waiting for possible tacacs timeout
        # it seems that old code is better than a new one -> _discover_prompt()
        self._discover_prompt()  # Raises exception if cant' discover prompt
        return True

    def _discover_prompt(self):
        """
        Discovers command prompt. Or configure prompt. Send Enter <CR> and waits wor result

        :return:
        """
        self.l.debug('_discover_prompt()')
        if not self.is_connected:
            raise NotConnected
        while True:
            pager_found = False
            self.send('')  # sending empty command (ENTER key)
            out = self.t.read_until(b'whatever?', self.io_timeout)  # waiting for io_timeout for command prompt
            out = out.replace(b'\x1b[K', b'')
            """
            Thx to https://jcastellssala.com/2012/07/20/python-command-line-waiting-feedback-and-some-background-on-why/
            \r Escape sequence for a Carriage Return (Go to the beginning of the line).
            \x1b[ Code for CSI (Control Sequence Introducer, nothing to do with the TV-series. check Wikipedia). 
            It is formed by the hexadecimal escape value 1b (\x1b) followed by [.
            K is the Escape sequence code to Erase the line.
            """
            self._print_recv(b2a(out))  # reading it
            if out is not b"":
                self.prompt = b2a(out).splitlines()[-1]  # getting it
            else:
                self.l.error("Command prompt cant be empty at " + self.ip)
                raise BadCommandPrompt
            if re.search(r'(\*)+', self.prompt, re.MULTILINE):
                # We have found * (asterisk character) in command prompt. Usually this is masked password.
                # So we cant handle it.
                self.l.error("We have found * (asterisk character) in command prompt. Usually this is masked password.")
                raise BadCommandPrompt
            # We need to check if pager string found in output
            for pager in self.pager:
                # self.l.debug(pager)
                # self.l.debug(out)
                if re.search(pager, out):
                    self.l.debug("found pager string! Sending SPACE at " + self.ip)
                    if not pager_found:  # only once per while loop
                        self.send(' ')  # sending space
                    pager_found = True
            if not pager_found:
                break  # exiting while loop
        self.l.debug("Discovered the prompt at %s: " % self.ip + c.BOLD + c.WHITE + self.prompt + c.RESET)
        self.is_logged = True
        return self.prompt

    @staticmethod
    def _multiline_search(search, where):
        """
        Performs multiline register-independent search and returns found value or False

        :param search: regexp to search with capture group (!) in it

        :param where: string where to search

        :return: None if not found or match
        """
        result_match_object = re.search(search, where, re.M | re.I)
        if result_match_object:
            return result_match_object.groups()[0]  # first match

        return None

    def _put_model_and_hostname(self, model, hostname, sw_version=None):
        if hostname:
            self.equipment_object.hostname = hostname
            self.l.debug("found hostname: %s" % hostname)
        if model:
            self.equipment_object.model = model.strip()
            self.l.debug("found model: %s" % model)
        if sw_version:
            self.equipment_object.sw_version = sw_version
            self.l.debug("found sw_version: %s" % sw_version)

    def discover_vendor(self):
        """
        Puts some commands to NE for discovering vendor of it. If discovering was successful than writing to DB

        NB: must be logged in

        :return: Vendor_Name (Cisco, Juniper, etc) if discovering were successful, or False otherwise
        """
        self.l.debug("Trying to discover vendor for: %s." % self.ip)
        if not self.is_logged:
            self.l.error("Must be logged in before vendor discovery")
            return False  # Must be logged in
        found_vendor = False
        try:
            # CISCO, SNR, Juniper guessing
            show_version_command_output = self.exec_cmd('show ver')
            if self._multiline_search(r'(JUNOS)', show_version_command_output):
                self.l.info("Juniper device found at IP: %s" % self.ip)
                found_vendor = 'Juniper'
                hostname = self._multiline_search(r'Hostname: (\S+)', show_version_command_output)
                model = self._multiline_search(r'Model: (\S+)', show_version_command_output)
                sw_version = self._multiline_search(r'(?:)\[(.+)\]', show_version_command_output)
                self._put_model_and_hostname(model, hostname, sw_version)
            elif self._multiline_search(r'(Cisco)', show_version_command_output):
                self.l.info("Cisco device found at IP: %s" % self.ip)
                found_vendor = 'Cisco'
                hostname = self._multiline_search(r'(\S+) uptime is .+', show_version_command_output)
                # If no hostname is found, eg PIX device, but we are pretty sure about cisco device, then we will use
                # prompt.
                if hostname is None:
                    hostname = self.prompt.strip()[:-1]
                    print("'" + hostname + "'")
                model = self._multiline_search(r'(.+) \(.+\) processor .+', show_version_command_output)
                sw_version = self._multiline_search(r'System image file is "(?:flash:|disk2:)\/*(.+)"',
                                                    show_version_command_output)
                self._put_model_and_hostname(model, hostname, sw_version)
            elif self._multiline_search(r'(SNR|NAG)', show_version_command_output):
                self.l.info("SNR device found at IP: %s" % self.ip)
                found_vendor = 'SNR'
                hostname = self._multiline_search(r'(\S+)#', show_version_command_output)
                model = self._multiline_search(r'(\S+) Device', show_version_command_output)
                sw_version = self._multiline_search(r'SoftWare Version (.+)', show_version_command_output)
                self._put_model_and_hostname(model, hostname, sw_version)
            elif re.search(r'raisecom', show_version_command_output, re.M | re.I):
                self.l.info("Raisecom device found at IP: %s" % self.ip)
                found_vendor = 'Raisecom'
            if not found_vendor:
                # Alcatel guessing
                show_version_command_output = self.exec_cmd('show equipment isam')
                if re.search(r'isam table', show_version_command_output, re.MULTILINE):
                    self.l.info("Alcatel device found at IP: %s" % self.ip)
                    found_vendor = 'Alcatel'
                    try:
                        astu = ASTU.objects.get(ne_ip=self.ip)
                        self.equipment_object.model = astu.model
                        self.equipment_object.hostname = astu.hostname
                        self.l.debug("Alcatel DSLAM, using ASTU fallback. Hostname: %s, model: %s"
                                     % (astu.hostname, astu.model))
                    except ASTU.DoesNotExist:
                        self.l.warning("Can't fallback to ASTU DB.")
            if not found_vendor:
                # Zyxel ZYNOS guessing
                show_version_command_output = self.exec_cmd('sys info show')
                if re.search(r'ZyNOS', show_version_command_output, re.MULTILINE):
                    self.l.info("Zyxel device found at IP: %s" % self.ip)
                    found_vendor = 'Zyxel'
                    hostname = self._multiline_search(r'Hostname: (\S+)', show_version_command_output)
                    model = self._multiline_search(r'Model: (\S+)', show_version_command_output)
                    sw_version = self._multiline_search(r'ZyNOS version: (.+)', show_version_command_output)
                    self._put_model_and_hostname(model, hostname, sw_version)
            if not found_vendor:
                # Eltex guessing
                # self.exec_cmd('terminal datadump')
                show_version_command_output = self.exec_cmd('show system')
                if self._multiline_search(r'(System Description)', show_version_command_output):
                    self.l.info("Eltex device found at IP: %s" % self.ip)
                    found_vendor = 'Eltex'
                    hostname = self._multiline_search(r'System Name:.+ (\S.+)', show_version_command_output)
                    model = self._multiline_search(r'System Description: (.+)', show_version_command_output)
                    # one more 'show ver' command to determine software version
                    show_version_command_output = self.exec_cmd('\nshow version')
                    self.l.info(show_version_command_output)
                    sw_version = self._multiline_search(r'SW version (.+) \(.+', show_version_command_output)
                    self._put_model_and_hostname(model, hostname, sw_version)
            if not found_vendor:
                # Huawei guessing
                self.set_io_timeout(2)  # Some Huawei OLT's is slow
                show_version_command_output = self.exec_cmd('display version\n')
                self._print_recv(show_version_command_output)
                if self._multiline_search(r'(HUAWEI)', show_version_command_output):
                    self.l.info("Huawei device found at IP: %s" % self.ip)
                    found_vendor = 'Huawei'
                    hostname = self._multiline_search(r'<(.+)>', show_version_command_output)
                    model = self._multiline_search(r'Quidway (\S+)', show_version_command_output)
                    sw_version = self._multiline_search(r'Version (\d.+)', show_version_command_output)
                    self._put_model_and_hostname(model, hostname, sw_version)
                if self._multiline_search(r'(MA56)', show_version_command_output):
                    self.l.info('Huawei OLT device found at IP: %s' % self.ip)
                    found_vendor = 'Huawei OLT'
                    hostname = self._multiline_search(r'(.+)>', self.prompt)
                    model = self._multiline_search(r'PRODUCT : (.+)', show_version_command_output)
                    sw_version = self._multiline_search(r'VERSION : (.+)', show_version_command_output)
                    patch = self._multiline_search(r'PATCH.+: (.+)', show_version_command_output)
                    self._put_model_and_hostname(model, hostname, sw_version + ' ' + patch)
                self.set_io_timeout(1)  # reverting to default timeout
            if not found_vendor:
                # Linux guessing
                show_version_command_output = self.exec_cmd('uname -a')
                if re.search(r'Linux', show_version_command_output, re.MULTILINE):
                    self.l.info("Linux device found at IP: %s" % self.ip)
                    found_vendor = 'Linux'
            if not found_vendor:
                # DLink guessing
                show_version_command_output = self.exec_cmd('show switch')
                if re.search(r'Device Type ', show_version_command_output, re.MULTILINE):
                    self.l.info("DLink device found at IP: %s" % self.ip)
                    found_vendor = 'DLink'
        except EOFError:
            self.l.warning("Disconnected!")
            return False
        if found_vendor:
            self.equipment_object.vendor = found_vendor
            self.l.debug('Writing it to DB')
            self.equipment_object.save()
            return found_vendor
        return False

    def _get_config_with(self, cmd_list, timeout=30):
        # default 30 sec must be enough to most cases. Some CPU overloaded devices are really slow
        self.io_timeout = timeout
        current_config = ''
        # We can pass multiple commands to get config
        if (type(cmd_list) is list) or (type(cmd_list) is tuple):
            for cmd in cmd_list:
                current_config += self.exec_cmd(cmd)
        else:
            current_config = self.exec_cmd(cmd_list)
        self.io_timeout = 1  # reverting timeout

        if self.equipment_object.current_config == current_config:  # Checking if no changes was since last check:
            self.l.debug('%s. Configuration has not changed' % self.ip)
            return True

        self.l.debug('Writing config to DB')
        self.equipment_object.current_config = current_config
        self.equipment_object.save()

        # Creating archive configuration
        self.l.debug("Writing to config archive DB")
        eq_conf_object = EquipmentConfig(equipment_id=self.equipment_object, config=current_config)
        eq_conf_object.save()
        # self.l.debug(out)
        return current_config

    def get_config(self):
        self.l.debug('Trying to get config from NE')
        if self.equipment_object.vendor == 'Cisco' or self.equipment_object.vendor == 'SNR':
            self.exec_cmd('terminal length 0')  # disable pager
            cmds = ('show inv', 'show module', 'show version', 'show run')
            self._get_config_with(cmds)
            return True
        elif self.equipment_object.vendor == 'Juniper':
            cmds = ('show chassis hardware | no-more', 'show configuration | no-more')
            self._get_config_with(cmds)
            return True
        elif self.equipment_object.vendor == 'Huawei':
            self.io_timeout = 3
            self.exec_cmd('screen-width 500')
            self.exec_cmd('y')
            self.exec_cmd('screen-length 0 temporary')
            cmds = ('display elabel', 'display version', 'display current-configuration')
            self._get_config_with(cmds)
            return True
        elif self.equipment_object.vendor == 'Huawei OLT':
            self.exec_cmd('enable')
            self.exec_cmd('scroll 512')
            cmds = ('display board 0', 'display current-configuration\n')
            self._get_config_with(cmds)
            return True
        elif self.equipment_object.vendor == 'Eltex':
            self.exec_cmd('terminal datadump')
            self.exec_cmd('')
            self._get_config_with('show run')
            return True
        elif self.equipment_object.vendor == 'Alcatel':
            self._get_config_with('info configure flat | no-more', timeout=300)  # very long configuration retrieving
            return True
        elif self.equipment_object.vendor == 'Zyxel':
            self._get_config_with('config show all')
            return True
        else:
            self.l.warning("Can not get config from unknown vendor!")
            return False
