from net.models import Equipment, Credentials, EquipmentSuggestCredentials
from telnetlib import Telnet
import logging
import re
import socket
from net.equipment.exceptions import NoLoginPrompt, NoPasswordPrompt
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
    re.compile(b'Login incorrect', flags=re.I),  # juniper
    re.compile(b'Bad Password', flags=re.I),  # zyxel
    re.compile(b'Error: Failed to authenticate', flags=re.I),  # huawei no tacacs
    re.compile(b'Error: Password incorrect', flags=re.I),  # huawei
]


def setup_logger(name, verbosity=1):
    """
    Basic logger
    """
    # formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
    formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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
        self.io_timeout = 5
        if equipment_object.credentials:
            self.username = equipment_object.credentials.login
            self.passw = equipment_object.credentials.passw
        else:
            self.username = ''
            self.passw = ''

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
        True if suggest login and password attempts were successful
        """
        if resuggest is False and self.equipment_object.credentials:
            self.l.info('Credentials are already in the DB')
            return False
        credentials = Credentials.objects.all()  # every login/password pairs
        for credential in credentials:
            # if it was tested, length of this filter will be 0
            was_it_tested = len(EquipmentSuggestCredentials.objects.filter(credentials_id=credential.id, equipment_id=self.equipment_object.id))
            if was_it_tested != 0:
                self.l.debug("Credentials was tested earlier: %s / %s", credential.login, credential.passw)
                self.l.debug("Skipping this...")
                continue  # skipping this one
            # Trying to login with that creds:
            self.username = credential.login
            self.passw = credential.passw
            if not self.is_connected:
                self.connect()  # connecting
            try:
                if self.try_to_login():  # if login was successful
                    self.l.info('Credentials for %s discovered! L: %s, P: %s', self.ip, self.username, self.passw)
                    self.equipment_object.credentials = credential  # going to write that to DB
                    self.equipment_object.save()
                    return True
                else:  # In case of Authentication failed
                    # do not care about results
                    tested, created = EquipmentSuggestCredentials.\
                        objects.get_or_create(equipment_id=self.equipment_object, credentials_id=credential)
                    tested.was_checked=True
                    tested.save()
                    self.l.debug("Created EquipmentSuggestCredentials with was_cheked = True for equipment_id=%s, credentials_id=%s ",
                                 self.equipment_object.id, credential.id)
            except EOFError:
                self.l.info("Disconnected suddenly")
                # Unfortunately we can't be sure if disconnect were caused by invalid login or by other circumstances
                self.disconnect()
        self.l.info("Couldn't find suggested credentials")
        return False

    def expect(self, re_list):
        """
        Expecting to find some of RE's in input re_list.
        :param re_list:
        :return: Returns telnet output or False if not found
        """
        str = self.t.expect(re_list, self.io_timeout)
        if str[0] == -1:
            self.l.debug("can't find expected string. Input was: %s", str[2])
            # line below has very ugly output, so I have to comment it =)
            # self.l.debug("search was: %s", re_list)
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

    def print_recv(self, input_string):
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
        sleep(0.5)
        out = self.expect(LOGIN_PROMPTS)
        self.l.debug("expecting login prompt:")
        self.print_recv(out)
        if not out:  # we are expecting to see login prompt
            self.l.warning("Can't find login prompt")
            # raise NoLoginPrompt
        self.send(self.username)  # sending login
        sleep(1)
        out = self.expect(PASSWORD_PROMPTS)
        self.l.debug("Expecting password prompt:")
        self.print_recv(out)
        if not out:  # same for password
            self.l.warning("Can't find password prompt")
            raise NoPasswordPrompt
        self.send(self.passw)  # sending password
        sleep(4)
        self.l.debug("Expecting login or password prompt in case of authentication is failed")
        out = self.expect(LOGIN_PROMPTS + PASSWORD_PROMPTS + AUTHENTICATION_FAILED)
        print(out)
        self.print_recv(out)
        if out:  # if we are seeing login or password again - our creds are invalid
            self.l.warning('login "%s" and password "%s" for %s are invalid.', self.username, self.passw, self.ip)
            return False
        self.l.debug("Logged in with L: %s and P: %s", self.username, self.passw)
        return True
