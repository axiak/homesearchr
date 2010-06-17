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

from apthn.filters.views import email

from apthn.utils.caching import cacheview

__all__ = ('create_filter', 'create_filter_success', 'main')

price_re = re.compile(r'\$([.\d]+).*?\$([.\d]+)')


def create_filter_key(request, city="boston", template="createfilter.html", *args, **kwargs):
    if request.method == 'POST':
        return None
    return 'cf__%s%s' % (city, template)

@cacheview(create_filter_key)
def create_filter(request, city="boston", template="createfilter.html", initial={}, ContactForm=UserForm):
    city_info = settings.CITIES.get(city.lower())
    center = settings.CITY_CENTERS[city.lower()]

    if request.method == 'POST':
        contactform = ContactForm(request.POST, initial=initial)
        form = FilterForm(request.POST, initial=initial)
        if form.is_valid() and contactform.is_valid():
            cinfo = contactform.contactstring(request)
            locations = []
            atoms = map(float, request.POST.get('location-data').split(','))
            for i in range(0, len(atoms), 4):
                locations.append(((atoms[i], atoms[i + 1]),
                                 atoms[i + 2], atoms[i + 3]))

            m = price_re.search(request.POST.get('price'))
            lprice, hprice = map(float, m.groups())
            distances = []
            for item in locations:
                distances.extend(item[1:])

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
                distance_centers = [db.GeoPt(*x[0]) for x in locations],
                distances = distances,
                price = [int(lprice), int(hprice)],
                size_names = form.cleaned_data['size'],
                size_weights = [1.0] * len(form.cleaned_data['size']),
                **boolean_data
                )
            f.put()

            namecinfo = cinfo.replace('@', 'AT').replace('.', 'DOT')
            email.enqueue_notify(cinfo)
            return HttpResponseRedirect('../success/')
    else:
        context = {'form': FilterForm(),
                   'cform': ContactForm(),
                   'centerlat': center[0],
                   'centerlng': center[1],
                   'mapzoom': center[2],}

    context['AJAX_KEY'] = settings.GOOGLE_AJAX_KEYS.get(request.META['HTTP_HOST'].lower().split(':')[0])
    context['MAP_KEY'] = settings.GOOGLE_MAP_KEYS.get(request.META['HTTP_HOST'].lower().split(':')[0])

    return direct_to_template(request, template, context)

def create_filter_success(request, city="boston"):
    return direct_to_template(request, "createfilter-success.html")

@cacheview(lambda x: '')
def main(request):
    return direct_to_template(request, 'index.html',
                              {'user': request.user})
