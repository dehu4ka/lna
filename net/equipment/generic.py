from net.models import Equipment, Credentials
from telnetlib import Telnet
import logging
import re
import socket

handler = logging.StreamHandler()

def a2b(ascii_str):  # ascii to binary
    return ascii_str.encode('ascii')


def b2a(bin_string):  # binary to ascii
    return bin_string.decode('ascii', 'replace')



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
        if equipment_object.credentials:
            self.username = equipment_object.credentials.login
            self.passw = equipment_object.credentials.passw
        else:
            self.username = ''
            self.passw = ''

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
        if resuggest == False and self.equipment_object.credentials:
            self.l.info('Credentials are already in the DB')
            return False
        credentials = Credentials.objects.all()
        for credential in credentials:
            # Trying to login with that creds:
            self.username = credential.login
            self.passw = credential.passw
            self.connect() # connecting
            if self.login():  # if login was successful
                self.l.info('Credentials for %s discovered! L: %s, P: %s', self.ip, self.username, self.passw)
                self.equipment_object.credentials = credential  # going to write that to DB
                self.equipment_object.save()
                return True
            self.disconnect()
        self.l.info("Couldn't find suggested credentials")
        return False
