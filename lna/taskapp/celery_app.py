
import os
from celery import Celery
from django.apps import apps, AppConfig
from django.conf import settings
import time


if not settings.configured:
    # set the default Django settings module for the 'celery' program.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')  # pragma: no cover


app = Celery('lna')
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
app.conf.broker_url = 'redis://localhost:6379/0'
app.conf.timezone = 'Asia/Yekaterinburg'
app.conf.beat_scheduler = 'django_celery_beat.schedulers:DatabaseScheduler'
# app.conf.result_backend = 'redis'

"""
class CeleryConfig(AppConfig):
    name = 'lna.taskapp'
    verbose_name = 'Celery Config'

    def ready(self):
        # Using a string here means the worker will not have to
        # pickle the object when using Windows.
        app.config_from_object('django.conf:settings')
        installed_apps = [app_config.name for app_config in apps.get_app_configs()]
        app.autodiscover_tasks(lambda: installed_apps, force=True)

        if hasattr(settings, 'RAVEN_CONFIG'):
            # Celery signal registration
# Since raven is required in production only,
            # imports might (most surely will) be wiped out
            # during PyCharm code clean up started
            # in other environments.
            # @formatter:off
            from raven import Client as RavenClient
            from raven.contrib.celery import register_signal as raven_register_signal
            from raven.contrib.celery import register_logger_signal as raven_register_logger_signal
# @formatter:on

            raven_client = RavenClient(dsn=settings.RAVEN_CONFIG['DSN'])
            raven_register_logger_signal(raven_client)
            raven_register_signal(raven_client)


"""

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))  # pragma: no cover

