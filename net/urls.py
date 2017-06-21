from django.conf.urls import include, url
from .views import Demo, PickNE, DoTask

urlpatterns = [
    url(r'^demo$', Demo.as_view(), name='demo'),
    url(r'^pick_ne', PickNE.as_view(), name='pick_ne'),
    url(r'^do_task', DoTask.as_view(), name='do_task'),
]
