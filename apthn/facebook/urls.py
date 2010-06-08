from django.conf.urls.defaults import *
#from django.views.generic.simple import direct_to_template

urlpatterns = patterns('',
       (r'^/?$', 'apthn.facebook.views.main'),
       (r'^filters/create/success/?$', 'apthn.facebook.views.create_filter_success'),
       (r'^filters/create/(\w+)/?$', 'apthn.facebook.views.create_filter'),
)
