from django.conf.urls import include, url
from rest_framework import routers
from .views import NEViewSet

router = routers.DefaultRouter()
router.register(r'ne_list', NEViewSet)


urlpatterns = [
    url(r'^api-auth/', include('rest_framework.urls')),
    url(r'^', include(router.urls))

]
