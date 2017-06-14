from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic import TemplateView
from django.views import defaults as default_views
from .views import ADSLImport, ADSLView, FTTxView, GPONView, ASTUView, SearchView

urlpatterns = [
    url(r'^import$', ADSLImport.as_view(), name='import'),
    url(r'^adsl$', ADSLView.as_view(), name='adsl'),
    url(r'^fttx$', FTTxView.as_view(), name='fttx'),
    url(r'^gpon$', GPONView.as_view(), name='gpon'),
    url(r'^astu$', ASTUView.as_view(), name='astu'),
    url(r'^search', SearchView.as_view(), name='search'),

]
