from django.conf.urls import include, url
from rest_framework import routers
from .views import NEViewSet, ListVendors

router = routers.DefaultRouter()
router.register(r'ne_list', NEViewSet, 'ne_list')
router.register(r'vendors', ListVendors, 'vendors')


urlpatterns = [
    url(r'^api-auth/', include('rest_framework.urls')),
    url(r'^', include(router.urls))

]
