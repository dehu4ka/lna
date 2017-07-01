import logging
from channels import Group
from channels.sessions import channel_session
import json
from net.models import Job


log = logging.getLogger(__name__)


def form_json_to_send(text):
    pass

# Connected to websocket.connect
@channel_session
def ws_connect(message, task_id):
    message.reply_channel.send({
        "text": json.dumps({
            "action": "reply_channel",
            "reply_channel": message.reply_channel.name,
        })
    })

    job = Job.objects.get(pk=task_id)
    message.reply_channel.send ({
        'text': json.dumps({
            'job': job.id,
            'job_name': job.name,
            'job_status': job.status,
            'celery_od': job.celery_id

        })
    })
    Group("task_watcher_%s" % task_id).add(message.reply_channel)
    Group("task_watcher_%s" % task_id).send(
        {"text": json.dumps('someone is connected')}
    )



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
