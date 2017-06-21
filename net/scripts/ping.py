import subprocess


def ping(target):
    proc = subprocess.Popen(['ping', '-q', '-c', '3', target], stdout=subprocess.DEVNULL)
    proc.wait()
    if proc.returncode == 0:
        return True
    return False

def start(**kwargs):
    try:
        if kwargs['target']:
            return ping(kwargs['target'])
    except KeyError:
        return False
