from django.conf.urls.defaults import *

urlpatterns = patterns('',
        (r'^breakdown/?$', 'apthn.apts.views.count_breakdowns'),
        (r'^count/?$', 'apthn.apts.views.count_apts'),
        (r'^get/(\w+)/?$', 'apthn.apts.getapts.getapts'),
        (r'^get/(\w+)/(.+)/?$', 'apthn.apts.getapts.getapt'),
        (r'^clean/?$', 'apthn.apts.views.clean_apts'),
        (r'^list/(\w+)/json/?$', 'apthn.apts.views.apt_list')
)
