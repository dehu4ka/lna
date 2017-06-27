from django.conf.urls import include, url
from net.views import Demo, PickNE, DoTask, ActiveTasks, ArchiveTasks

urlpatterns = [
    url(r'^demo$', Demo.as_view(), name='demo'),
    url(r'^pick_ne', PickNE.as_view(), name='pick_ne'),
    url(r'^do_task', DoTask.as_view(), name='do_task'),
    url(r'^active_tasks', ActiveTasks.as_view(), name='active_tasks'),
    url(r'^archive_tasks', ArchiveTasks.as_view(), name='archive_tasks'),
]
