class NoLoginPrompt(Exception):
    def __init__(self):
        Exception.__init__(self, "There was no _known_ login prompt!")


class NoPasswordPrompt(Exception):
    def __init__(self):
        Exception.__init__(self, "There was no _known_ login prompt!")


class NoKnownPassword(Exception):
    def __init__(self):
        Exception.__init__(self, "Trying to login with unknown password")
