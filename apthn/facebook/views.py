from django.http import HttpResponse
from django.views.generic.simple import direct_to_template

import facebook.djangofb as facebook

from apthn.filters import views as filterviews
from apthn.facebook.forms import FacebookContactForm
from apthn.utils.caching import cacheview

def login_path(path):
    path = 'http://www.homesearchr.com%s/' % path.rstrip('/')
    return path

def facebook_url(request):
    return '%s/' % request.path.lstrip('/').split('/', 1)[0]

def create_filter_key(request, city="boston", initial={}):
    if request.method == 'POST':
        return None
    return 'fb_create_filter_%s' % city

def create_filter_success(request, city="boston"):
    return direct_to_template(request, "facebook/createfilter-success.html")

@facebook.require_login()
@cacheview(create_filter_key)
def create_filter(request, city="boston", initial={}):
    return filterviews.create_filter(request, city, "facebook/createfilter.html", initial=initial)

@facebook.require_login(next=login_path)
@cacheview(lambda x: 'fb_main')
def main(request):
    return direct_to_template(request, 'facebook/index.html', {"FACEBOOK_URL": facebook_url(request)})
