from net.models import Equipment, Credentials
from telnetlib import Telnet
import logging
import re

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
    def __init__(self, equipment_object_reference):
        if not isinstance(equipment_object_reference, Equipment):
            raise Exception("Passed to constructor not Equipment Object")
        self.ip = equipment_object_reference.ne_ip
        self.l = setup_logger('net.equipment.generic', 2)  # 2 means debug



    def work(self):
        self.l.debug('work')

