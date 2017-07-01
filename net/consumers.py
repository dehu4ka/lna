import logging
from channels import Group
from channels.sessions import channel_session
import json
from net.models import Job, JobResult


log = logging.getLogger(__name__)


# Connected to websocket.connect
@channel_session
def ws_connect(message, task_id):
    job = Job.objects.get(pk=task_id)
    job_result, created = JobResult.objects.get_or_create(job_id=job)

    message.reply_channel.send ({
        'text': json.dumps({
            'job': job.id,
            'script_name': job.script_name,
            'result': job_result.result,
            'status': job.status,
            'celery_id': job.celery_id
        })
    })
    Group("task_watcher_%s" % task_id).add(message.reply_channel)


# Connected to websocket.receive
@channel_session
def ws_message(message, task_id):
    try:
        data = json.loads(message['text'])
    except ValueError:
        log.debug("ws message isn't json text=%s", message['text'])
        return

# Connected to websocket.disconnect
@channel_session
def ws_disconnect(message, task_id):
    Group("task_watcher_%s" % task_id).discard(message.reply_channel)
    Group("task_watcher_%s" % task_id).send(
        {"text": json.dumps('someone is disconnected')}
    )
