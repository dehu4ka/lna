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
    def __init__(self):
        Exception.__init__(self, "Trying to exec commands without logged in to device")


class BadCommandPrompt(Exception):
    def __init__(self):
        Exception.__init__(self, "Bad command/shell prompt discovered. Check timeouts and login credentials")


class NotConnected(Exception):
    def __init__(self):
        Exception.__init__(self, "Trying to do something on device without connection.")
