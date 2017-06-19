from django.conf.urls import include, url
from .views import Demo, PickNE

urlpatterns = [
    url(r'^demo$', Demo.as_view(), name='demo'),
    url(r'^pick-ne', PickNE.as_view(), name='pick_ne')
]
