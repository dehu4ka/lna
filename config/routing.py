from channels.routing import route
from net.consumers import ws_connect, ws_message, ws_disconnect

channel_routing = [
    route("websocket.connect", ws_connect, path=r'/ws/active_tasks/(?P<task_id>[a-zA-Z0-9_]+)/$'),
    route("websocket.receive", ws_message, path=r'/ws/active_tasks/(?P<task_id>[a-zA-Z0-9_]+)/$'),
    route("websocket.disconnect", ws_disconnect, path=r'/ws/active_tasks/(?P<task_id>[a-zA-Z0-9_]+)/$'),
]
