import logging
from .base import BaseScript



log = logging.getLogger(__name__)


def suggest_job():
    log.warning('login_suggest.py suggest_job')


class LoginSuggest(BaseScript):
    name = "Suggest Login & Password"
    description = "Fetches logins and passwords from DB and tries to login. If it was successful, stores result in DB"

    def work(self):
        log.warning("def work in LoginSuggest in login_suggest.py")


