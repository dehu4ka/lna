from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic import TemplateView
from django.views import defaults as default_views
from .views import ClientImport, ASTUView, SearchView

urlpatterns = [
    url(r'^import$', ClientImport.as_view(), name='import'),
    url(r'^astu$', ASTUView.as_view(), name='astu'),
    url(r'^find$', SearchView.as_view(), name='search'),

]
