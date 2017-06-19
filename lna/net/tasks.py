import time
from lna.taskapp.celery import app


@app.task()
def long_job(job_id, reply_channel):
    pass
