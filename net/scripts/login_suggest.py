from celery import current_task, shared_task, states
import logging
from .base import BaseScript
from lna.taskapp.celery_app import app as celery_app



log = logging.getLogger(__name__)


def suggest_job():
    log.warning('login_suggest.py suggest_job')


class LoginSuggest(BaseScript):
    name = "Suggest Login & Password"
    description = "Fetches logins and passwords from DB and tries to login. If it was successful, stores result in DB"

    def work(self):
        log.warning("def work in LoginSuggest in login_suggest.py")


@celery_app.task(bind=True)
def login_suggest_task(self):
    log.warning('celery task in login_suggest.py')
