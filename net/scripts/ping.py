import subprocess
from .base import BaseScript
import logging


log = logging.getLogger(__name__)


def ping(target):
    # proc = subprocess.Popen(['ping', '-q', '-c', '3', target], stdout=subprocess.DEVNULL)
    proc = subprocess.Popen(['fping', '-q', '-O', '160', target], stdout=subprocess.DEVNULL)
    proc.wait()
    if proc.returncode == 0:
        return True
    return False


def start(**kwargs):
    try:
        if kwargs['target']:
            return ping(kwargs['target'])
    except KeyError:
        return


class PingScript(BaseScript):
    name = "ping"
    description = "Pings Targets"

    def __init__(self, target):
        self.target = target
        self.work()

    def work(self):
        proc = subprocess.Popen(['fping', '-q', '-O', '160', self.target], stdout=subprocess.DEVNULL)
        proc.wait()
        if proc.returncode == 0:
            return True
        return False



