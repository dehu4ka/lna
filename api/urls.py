from django.conf.urls import include, url
from rest_framework import routers
from api.views import NEViewSet, ListVendors, ListModels

router = routers.DefaultRouter()
router.register(r'ne_list', NEViewSet, 'ne_list')
router.register(r'vendors', ListVendors, 'vendors')
router.register(r'models', ListModels, 'models')


urlpatterns = [
    url(r'^api-auth/', include('rest_framework.urls')),
    url(r'^', include(router.urls))

]
