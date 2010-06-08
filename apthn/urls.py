from django.conf.urls.defaults import *
#from django.views.generic.simple import direct_to_template

urlpatterns = patterns('',
       (r'^apts/', include('apthn.apts.urls')),
       (r'^filters/', include('apthn.filters.urls')),
       (r'^/?$', 'apthn.filters.views.main'),
       (r'^fb/', include('apthn.facebook.urls')),
)
