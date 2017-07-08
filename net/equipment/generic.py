from net.models import Equipment, Credentials, EquipmentSuggestCredentials
from telnetlib import Telnet
import logging
import re
import socket
from net.equipment.exceptions import NoLoginPrompt, NoPasswordPrompt, NoKnownPassword, NoLoggedIn
from time import sleep
from net.libs.colors import Colors

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

]

PASSWORD_PROMPTS = [
    re.compile(b'pass: ', flags=re.I),
    re.compile(b'pass:', flags=re.I),
    re.compile(b'password: ', flags=re.I),
    re.compile(b'password:', flags=re.I),
]

AUTHENTICATION_FAILED = [
    re.compile(b'Authentication failed', flags=re.I),  # cisco
    re.compile(b'Password incorrect', flags=re.I),  # cisco
    re.compile(b'Login incorrect', flags=re.I),  # juniper
    re.compile(b'Bad Password', flags=re.I),  # zyxel
    re.compile(b'Error: Failed to authenticate', flags=re.I),  # huawei no tacacs
    re.compile(b'Error: Password incorrect', flags=re.I),  # huawei
    re.compile(b'Invalid user name and password', flags=re.I),  # SNR
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
    def __init__(self, equipment_object):
        if not isinstance(equipment_object, Equipment):
            raise Exception("Passed to constructor not Equipment Object")
        self.equipment_object = equipment_object
        self.ip = equipment_object.ne_ip
        self.l = setup_logger('net.equipment.generic', 2)  # 2 means debug

        self.l.debug('Equipment object was created, IP: %s', self.ip)
        self.timeout = 3  # telnet timeout in seconds
        self.t = Telnet()
        self.is_connected = False
        self.prompt = ''  # приглашение командной строки
        self.config = None  # забранный конфиг
        self.pager = self.init_pager()
        self.is_logged = False  # удалось ли авторизоваться
        self.in_configure_mode = False
        self.io_timeout = 0.5  # timeout between entering CMD and waiting for output
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
        try:
            self.t.open(self.ip, 23, self.timeout)
        except ConnectionRefusedError:
            self.l.warning("Connection to %s is refused!", self.ip)
            return False
        except socket.timeout:
            self.l.warning("Connection to %s - timeout!", self.ip)
            return False
        else:
            self.l.debug('Connection to %s was successful', self.ip)
            self.is_connected = True
            return True

    def disconnect(self):
        self.is_connected = False  # pointless ?
        self.is_logged = False
        self.t.close()

    def login(self, login_timeout=0.4):
        #  Задумка в том что тупо шлём пару логин / пароль
        #  Величина login_timeout зависит имхо от задержки такакса
        try:
            self.t.write(a2b(self.username + "\n"))  # login
            #  Ждём того что никогда не будет с таймаутом 0.2 мс
            self.t.read_until(b'whatever?', login_timeout)
            self.t.write(a2b(self.passw + "\n"))  # pass
            output = self.t.read_until(b'whatever?', login_timeout)
            # print(output)
            self.t.write(a2b("\n"))  # Enter
            output = self.t.read_until(b'whatever?', login_timeout)
            # print(output)
            self.t.write(a2b("\n"))  # Enter
            output = self.t.read_until(b'whatever?', login_timeout)
            # print(output)
            self.prompt = b2a(output).splitlines()[-1]
            self.l.debug('Discovered prompt is: %s', self.prompt)
            self.is_logged = True
            return True
        except IndexError:
            self.l.error('Can not login to NE, login incorrect or auth timeout')
            return False
        except ConnectionResetError:
            self.l.error('ConnectionResetError!')
        except KeyboardInterrupt:
            self.t.close()
            self.l.error("Keyboard interrupt exception")
            return False

    def suggest_login(self, resuggest=False):
        """
        Подбирает логин и пароль из списка в БД
        :param resuggest: If we already have credentials in the DB and still want to try new suggestions
        :return:
        Dict with IP, Login, Pass if suggestion was successful
        False if we can't suggest login/pass
        """
        if resuggest is False and self.equipment_object.credentials:
            self.l.info('Credentials are already in the DB')
            return {
                        'ip': self.ip,
                        'login': self.username,
                        'password': self.passw
                    }
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
            self.l.info("SUGGESTING LOGIN | Trying to login with L: %s, P: %s" % (c.YELLOW + credential.login + c.RESET,
                                                                                  c.PURPLE + credential.passw +
                                                                                  c.RESET))
            self.username = credential.login
            self.passw = credential.passw
            if not self.is_connected:
                if not self.connect():  # connecting
                    self.l.warning("Can't connect, so we can't suggest login.")
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
            except NoPasswordPrompt:
                self.l.info("Disconnected suddenly. No Password Prompt were detected")
                self.disconnect()
            except NoLoginPrompt:
                self.l.info("Disconnected suddenly. No Login Prompt were detected")
                self.disconnect()
        self.l.warning("%sCouldn't find suggested credentials%s" % (c.CYAN + c.BOLD, c.RESET))
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
        :param re_list:
        :return: Returns telnet output or False if not found
        """
        str = self.t.expect(re_list, self.io_timeout)
        if str[0] == -1:
            self.l.debug("can't find expected string in string: %s", str[2])
            # line below has very ugly output, so I have to comment it =)
            # self.l.debug("search was: %s", re_list)
            self._print_recv(b2a(str[2]))
            return False  # not found
        # otherwise string is found, returning it ascii
        return b2a(str[2])
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
            raise NoLoggedIn
        output = ''  # all output in ascii will be here
        self.l.debug('>>>> sending')
        self.l.debug(c.RED + c.BOLD + cmd + c.RESET)
        self.t.write(a2b(cmd + "\n"))
        self.l.debug('>>>> sending end')
        expect_list = self.pager
        expect_list.append(a2b(self.prompt))  # If we have in our expect list both shell prompt and more prompt,
        #  we should not wait too long
        while True:
            out = self.t.expect(self.pager, self.io_timeout)
            output += b2a(out[2])
            if out[0] == -1:
                break
            x = re.compile(a2b(self.prompt))
            if out[1].re != x:
                self.t.write(a2b(' '))  # sending SPACE to get next page
        return output

    def _print_recv(self, input_string):
        """
        Prints received output to console
        :param input_string: string to color in debug output
        :return:
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
        :return: False if login attempt was unsuccessful, otherwise - True
        """
        self._sleep(0.5)
        self.l.debug("expecting login prompt:")
        out = self.expect(LOGIN_PROMPTS)
        self._print_recv(out)
        if not out:  # we are expecting to see login prompt
            self.l.warning("Can't find login prompt")
            # raise NoLoginPrompt
        self.send(self.username)  # sending login
        self._sleep(1)
        self.l.debug("Expecting password prompt:")
        out = self.expect(PASSWORD_PROMPTS)
        self._print_recv(out)
        if not out:  # same for password
            self.l.warning("Can't find password prompt")
            raise NoPasswordPrompt
        self.send(self.passw)  # sending password
        self._sleep(2)  # 2 seconds because most equipment have big timeout after unsuccessful login
        self.l.debug("Expecting login or password prompt or auth failed in case of authentication is failed")
        out = self.expect(LOGIN_PROMPTS + PASSWORD_PROMPTS + AUTHENTICATION_FAILED)
        self._print_recv(out)
        if out:  # if we are seeing login or password again - our creds are invalid
            self.l.warning('login "%s" and password "%s" for %s are invalid.', self.username, self.passw, self.ip)
            return False
        self.l.debug("Logged in with L: %s and P: %s", self.username, self.passw)
        return True

    def do_login(self):
        """
        Assuming that we are already know valid login and password from login_suggest.
        So, we need to login to device
        :return: True. Or Exception if something was wrong
        """
        if self.passw is None:
            raise NoKnownPassword
        if self.is_connected:
            self.disconnect()
        self.connect()  # connecting
        out = self.expect(LOGIN_PROMPTS)  # we need to wait for login prompt
        self._print_recv(out)  # debug out
        self.send(self.username)  # sending known username
        out = self.expect(PASSWORD_PROMPTS)  # waiting for password prompt
        self._print_recv(out)  # debug out
        self.send(self.passw)  # sending known password
        self._sleep(0.5)  # waiting for possible tacacs timeout
        self.is_logged = True
        # it seems that old code is better than a new one -> _discover_prompt()
        self._discover_prompt()
        return True

    def _discover_prompt(self):
        """
        Discovers commant prompt. Or configure prompt. Send Enter <CR> and waits wor result
        :return:
        """
        if not self.is_logged:
            raise NoLoggedIn
        self.send('')  # sending empty command
        out = self.t.read_until(b'whatever?', self.io_timeout)  # wainting for io_timeout for command promt
        self._print_recv(b2a(out))  # reading it
        self.prompt = b2a(out).splitlines()[-1]  # getting it
        self.is_logged = True
        self.l.debug("Discovered the prompt: " + c.BOLD + c.WHITE + self.prompt + c.RESET)
        return self.prompt

    def discover_vendor(self):
        sh_ver = self.exec_cmd('show ver')
        # print(sh_ver)
        # NAG/SNR check
        if re.search(r'(SNR|NAG)', sh_ver, re.MULTILINE):
            self.l.info("SNR device found")
        if re.search(r'Cisco', sh_ver, re.MULTILINE):
            self.l.info("Cisco device found")
        if re.search(r'JUNOS', sh_ver, re.MULTILINE):
            self.l.info("Juniper device found")
