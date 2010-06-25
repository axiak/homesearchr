from django.conf.urls.defaults import *

urlpatterns = patterns('',
        (r'^disable/(.+?)/?$', 'apthn.filters.views.disable.disable_filter'),
        (r'^create/success/?$', 'apthn.filters.views.create_filter_success'),
        (r'^create/(\w+)/?$', 'apthn.filters.views.create_filter'),
        (r'^estimate-traffic/?$', 'apthn.filters.views.ajax.ajax_get_count'),

        (r'^email/all/?$', 'apthn.filters.views.email.send_emails'),
        (r'^email/one/?$', 'apthn.filters.views.email.send_one_email'),

        (r'^admin/(.+?)/?$', 'apthn.filters.views.admin.filter_info'),
        (r'^admin/?$', 'apthn.filters.views.admin.filter_view'),
)
