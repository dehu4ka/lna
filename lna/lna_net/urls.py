from django.conf.urls import include, url
from .views import Demo

urlpatterns = [
    url(r'^demo$', Demo.as_view(), name='demo')
]
