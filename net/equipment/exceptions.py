class NoLoginPrompt(Exception):
    def __init__(self):
        Exception.__init__(self, "There was no _known_ login prompt!")


class NoPasswordPrompt(Exception):
    def __init__(self):
        Exception.__init__(self, "There was no _known_ login prompt!")


class NoKnownPassword(Exception):
    def __init__(self):
        Exception.__init__(self, "Trying to login with unknown password")


class NotLoggedIn(Exception):
    def __init__(self, ip):
        Exception.__init__(self, "Trying to exec commands without logged in to device with IP: %s" % ip)


class BadCommandPrompt(Exception):
    def __init__(self, ip):
        Exception.__init__(self, "Bad command/shell prompt discovered on %s. Check timeouts and login credentials" % ip)


class NotConnected(Exception):
    def __init__(self, ip):
        Exception.__init__(self, "Trying to do something on device %s without connection." % ip)
