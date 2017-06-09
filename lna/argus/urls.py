from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic import TemplateView
from django.views import defaults as default_views
from .views import ADSL_Import, ADSL_View

urlpatterns = [
    url(r'^import$', ADSL_Import.as_view(), name='import'),
    url(r'^adsl$', ADSL_View.as_view(), name='adsl'),
]
