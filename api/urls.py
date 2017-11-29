from django.conf.urls import include, url
from rest_framework import routers
from api.views import NEViewSet, ListVendors, ListModels, ListTasks, NEDetail, ArchiveConfig, ConfigDiff

router = routers.DefaultRouter()
router.register(r'ne_list', NEViewSet, 'ne_list')
router.register(r'vendors', ListVendors, 'vendors')
router.register(r'models', ListModels, 'models')
router.register(r'tasks', ListTasks, 'tasks')
# router.register(r'ne_detail', NEDetail, 'ne_detail')


urlpatterns = [
    url(r'^api-auth/', include('rest_framework.urls')),
    url(r'ne_detail/(?P<pk>[0-9]+)/$', NEDetail.as_view()),
    url(r'get_archived_config/(?P<pk>[0-9]+)/$', ArchiveConfig.as_view()),
    url(r'get_config_diff/(?P<pk>[0-9]+)/(?P<pk2>[0-9]+)/$', ConfigDiff.as_view()),
    url(r'^', include(router.urls))

]
