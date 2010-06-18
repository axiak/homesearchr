import re
import datetime

from google.appengine.ext import db

from django.views.generic.simple import direct_to_template
from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseRedirect

from apthn.users.decorators import login_required
from apthn.filters.forms import FilterForm, EmailForm
from apthn.filters.models import AptFilter
from apthn.users.models import AptHunter
from apthn.users.forms import UserForm

from apthn.filters.views import email

from apthn.utils.caching import cacheview

__all__ = ('create_filter', 'create_filter_success', 'main')

price_re = re.compile(r'\$([.\d]+).*?\$([.\d]+)')


def create_filter_key(request, city="boston", template="createfilter.html", *args, **kwargs):
    if request.method == 'POST':
        return None
    return 'cf_%s%s' % (city, template)

@cacheview(create_filter_key)
def create_filter(request, city="boston", template="createfilter.html", initial={}, ContactForm=UserForm):
    city_info = settings.CITIES.get(city.lower())
    center = settings.CITY_CENTERS[city.lower()]

    contactform = ContactForm(request.POST or None, initial=initial)
    form = FilterForm(request.POST or None, initial=initial)
    if form.is_valid() and contactform.is_valid():
        cinfo = contactform.contactstring(request)

        m = price_re.search(request.POST.get('price'))
        lprice, hprice = map(float, m.groups())

        apth = AptHunter.all().filter("contactinfo =", cinfo)
        apth = apth.get()
        if apth:
            # Deactivate any old ones
            q = AptFilter.all().filter("apth =", apth)
            q.filter("active =", True)
            for result in q.fetch(1000):
                result.active = False
                result.disable_status = "Replaced, Replaced"
                result.put()

        boolean_data = {}
        for key in ('cats', 'concierge', 'washerdryer', 'heat', 'hotwater',
                    'brokerfee'):
            boolean_data[key] = int(form.cleaned_data[key])

        apth = AptHunter(key_name=cinfo,
                         contactinfo=cinfo,
                         first_created=datetime.datetime.now())
        apth.put()

        # Create Filter
        f = AptFilter(
            active = True,
            apth = apth,
            region = city.upper(),
            expires = form.cleaned_data['expires'],
            distance_centers = [], # Disabled
            distances = [], # Disabled
            polygons = request.POST["location-data"],
            price = [int(lprice), int(hprice)],
            size_names = form.cleaned_data['size'],
            size_weights = [1.0] * len(form.cleaned_data['size']),
            **boolean_data
            )
        f.put()

        namecinfo = cinfo.replace('@', 'AT').replace('.', 'DOT')
        email.enqueue_notify(cinfo)
        response = HttpResponseRedirect('../success/')
        user = AptHunter.make_user(contactform)
        user.last_city = city
        db.put(user)
        response.set_cookie("sessioncookie", user.sessioncookie)
        response.set_cookie("username", user.username)
        return response

    if not request.user:
        cform = ContactForm()
    else:
        cform = None

    context = {'form': FilterForm(),
               'cform': cform,
               'centerlat': center[0],
               'centerlng': center[1],
               'mapzoom': center[2],}

    context['AJAX_KEY'] = settings.GOOGLE_AJAX_KEYS.get(request.META['HTTP_HOST'].lower().split(':')[0])
    context['MAP_KEY'] = settings.GOOGLE_MAP_KEYS.get(request.META['HTTP_HOST'].lower().split(':')[0])
    context["CITY"] = city
    return direct_to_template(request, template, context)

def create_filter_success(request, city="boston"):
    return direct_to_template(request, "createfilter-success.html")

@cacheview(lambda x: '')
def main(request):
    return direct_to_template(request, 'index.html',
                              {'user': request.user})
