lna
===

Lazy Network Admin

.. image:: https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg
     :target: https://github.com/pydanny/cookiecutter-django/
     :alt: Built with Cookiecutter Django


:License: MIT


Settings
--------

Moved to settings_.

.. _settings: http://cookiecutter-django.readthedocs.io/en/latest/settings.html

Basic Commands
--------------

Setting Up Your Users
^^^^^^^^^^^^^^^^^^^^^

* To create a **normal user account**, just go to Sign Up and fill out the form. Once you submit it, you'll see a "Verify Your E-mail Address" page. Go to your console to see a simulated email verification message. Copy the link into your browser. Now the user's email should be verified and ready to go.

* To create an **superuser account**, use this command::

    $ python manage.py createsuperuser

For convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox (or similar), so that you can see how the site behaves for both kinds of users.

Test coverage
^^^^^^^^^^^^^

To run the tests, check your test coverage, and generate an HTML coverage report::

    $ coverage run manage.py test
    $ coverage html
    $ open htmlcov/index.html

Running tests with py.test
~~~~~~~~~~~~~~~~~~~~~~~~~~

::

  $ py.test

Live reloading and Sass CSS compilation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Moved to `Live reloading and SASS compilation`_.

.. _`Live reloading and SASS compilation`: http://cookiecutter-django.readthedocs.io/en/latest/live-reloading-and-sass-compilation.html



Celery
^^^^^^

This app comes with Celery.

To run a celery worker:

.. code-block:: bash

    cd lna
    celery -A lna.taskapp worker -l info
    or with flower
    celery -A lna.taskapp flower

Please note: For Celery's import magic to work, it is important *where* the celery commands are run. If you are in the same folder with *manage.py*, you should be right.

/etc/systemd/system/celery.service

.. code-block:: bash

    [Unit]
    Description=Celery Service
    After=network.target

    [Service]
    Type=forking
    User=hu4
    Group=hu4
    EnvironmentFile=-/etc/celery.conf
    WorkingDirectory=/home/hu4/lna
    ExecStart=/bin/sh -c '${CELERY_BIN} multi start $CELERYD_NODES \
        -A $CELERY_APP --logfile=${CELERYD_LOG_FILE} \
        --pidfile=${CELERYD_PID_FILE} $CELERYD_OPTS'
    ExecStop=/bin/sh -c '${CELERY_BIN} multi stopwait $CELERYD_NODES \
        --pidfile=${CELERYD_PID_FILE}'
    ExecReload=/bin/sh -c '${CELERY_BIN} multi restart $CELERYD_NODES \
        -A $CELERY_APP --pidfile=${CELERYD_PID_FILE} --logfile=${CELERYD_LOG_FILE} \
        --loglevel="${CELERYD_LOG_LEVEL}" $CELERYD_OPTS'

    [Install]
    WantedBy=multi-user.target

/etc/systemd/system/celerybeat.service
    [Unit]
    Description=Celery beat
    After=network.target celery.service

    [Service]
    Type=forking
    User=hu4
    Group=hu4
    EnvironmentFile=-/etc/celery.conf
    WorkingDirectory=/home/hu4/lna
    ExecStart=/bin/sh -c '${CELERY_BIN} beat -A ${CELERY_APP} --detach \
        --pidfile=${CELERYBEATD_PID_FILE} \
        --logfile=${CELERYBEATD_LOG_FILE} \
        --loglevel=${CELERYD_LOG_LEVEL} \
        -S django'
    ExecStop=/bin/systemctl kill celerybeat.service
    RemainAfterExit=yes

    [Install]
    WantedBy=multi-user.target

/etc/celery.conf

    # See
    # http://docs.celeryproject.org/en/latest/tutorials/daemonizing.html#available-options

    CELERY_APP="lna.taskapp.celery_app"
    CELERYD_NODES="worker1"
    CELERYD_OPTS="--concurrency=5 --time-limit=300"
    CELERY_BIN="/home/hu4/lna/.venv/bin/celery"
    CELERYD_PID_FILE="/var/run/celery/%n.pid"
    CELERYD_LOG_FILE="/var/log/celery/%n%I.log"
    CELERYD_LOG_LEVEL="INFO"
    CELERYD_MULTI="multi"

    CELERYBEATD_PID_FILE="/var/run/celerybeat/celerybeat.pid"
    CELERYBEATD_LOG_FILE="/var/log/celerybeat/celerybeat.log"
    CELERYBEATD_SHEDULE_FILE="/var/lib/celerybeat/celerybeat-shedule"



Email Server
^^^^^^^^^^^^

In development, it is often nice to be able to see emails that are being sent from your application. If you choose to use `MailHog`_ when generating the project a local SMTP server with a web interface will be available.

.. _mailhog: https://github.com/mailhog/MailHog

To start the service, make sure you have nodejs installed, and then type the following::

    $ npm install
    $ grunt serve

(After the first run you only need to type ``grunt serve``) This will start an email server that listens on ``127.0.0.1:1025`` in addition to starting your Django project and a watch task for live reload.

To view messages that are sent by your application, open your browser and go to ``http://127.0.0.1:8025``

The email server will exit when you exit the Grunt task on the CLI with Ctrl+C.




Sentry
^^^^^^

Sentry is an error logging aggregator service. You can sign up for a free account at  https://sentry.io/signup/?code=cookiecutter  or download and host it yourself.
The system is setup with reasonable defaults, including 404 logging and integration with the WSGI application.

You must set the DSN url in production.


Deployment
----------

The following details how to deploy this application.

Daphne channel layer
--------------------
    daphne -p 8080 config.asgi:channel_layer

Channels worker
---------------
    python manage.py runworker

Nginx config
------------

Guide at https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-centos-7

    server {
    listen 80;
    server_name 10.179.9.55;
    # no favicon warning<-->
    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        root /home/hu4/lna/lna;
    }

    location /ws/ {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 600s;
    }

    location / {
            proxy_set_header Host $http_host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
                proxy_pass http://unix:/home/hu4/lna/lna.sock;
        }
    }

Gunicorn
--------
/etc/systemd/system/gunicorn.service
sudo systemctl start gunicorn
sudo systemctl enable gunicorn

    [Unit]
    Description=gunicorn daemon
    After=network.target

    [Service]
    User=hu4
    Group=nginx
    WorkingDirectory=/home/hu4/lna
    ExecStart=/home/hu4/lna/.venv/bin/gunicorn --workers 3 --bind unix:/home/hu4/lna/lna.sock config.wsgi:application

    [Install]
    WantedBy=multi-user.target


