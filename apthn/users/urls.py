from django.conf.urls.defaults import *

urlpatterns = patterns('',
        (r'^login/?$', 'apthn.users.views.login'),
        (r'^forgot/?$', 'apthn.users.views.forgot'),
        (r'^wheredoyouwanttogotoday/?$', 'apthn.users.views.wheredoyouwanttogotoday')
)
