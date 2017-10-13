from django.conf.urls import include, url
from net.views import Demo, PickNE, DoTask, ActiveTasks, ArchiveTasks, TaskDetail, DiscoverSubnets, ClientsCount, \
    NEList, NEDetail, SubnetsList

urlpatterns = [
    url(r'^demo$', Demo.as_view(), name='demo'),
    url(r'^pick_ne', PickNE.as_view(), name='pick_ne'),
    url(r'^do_task', DoTask.as_view(), name='do_task'),
    url(r'^active_tasks', ActiveTasks.as_view(), name='active_tasks'),
    url(r'^archive_tasks', ArchiveTasks.as_view(), name='archive_tasks'),
    url(r'^task_detail/(?P<task_id>[0-9]+)/$', TaskDetail.as_view(), name='task_detail'),
    url(r'^discover_subnets$', DiscoverSubnets.as_view(), name='discover_subnets'),
    url(r'^clients_count$', ClientsCount.as_view(), name='clients_count'),
    url(r'^ne_list', NEList.as_view(), name='ne_list'),
    url(r'^ne_detail/(?P<pk>[0-9]+)/$', NEDetail.as_view(), name='ne_detail'),
    url(r'subnets', SubnetsList.as_view(), name='subnets_list')
]
