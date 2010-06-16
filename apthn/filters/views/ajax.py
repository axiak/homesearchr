import re
import logging
import datetime

from google.appengine.api import memcache
from google.appengine.ext import db

from django.http import HttpResponse
from django.utils import simplejson

from apthn.filters.models import AptFilter

from apthn.filters.views import email

price_re = re.compile(r'\$([.\d]+).*?\$([.\d]+)')
look_back = datetime.datetime.now() - datetime.timedelta(days=2)

def ajax_get_count(request):
    city = request.META['HTTP_REFERER'].split('?')[0].rstrip('/').split('/')[-1]

    m = price_re.search(request.POST.get('price'))
    lprice, hprice = map(float, m.groups())
    cinfo = request.POST.get('email')

    boolean_data = {}
    for key in ('cats', 'concierge', 'washerdryer', 'heat', 'hotwater',
                'brokerfee'):
        boolean_data[key] = int(request.POST[key])

    sizes = request.POST['size_data'].split(',')

    # Create Filter
    f = AptFilter(
        active = True,
        region = city.upper(),
        distance_centers = [],
        distances = [],
        polygons = request.POST['location-data'],
        price = [int(lprice), int(hprice)],
        size_names = sizes,
        size_weights = [1.0] * len(sizes),
        **boolean_data
        )
    logging.info("Filter: %r" % f.__dict__)
    results, scanned = email.get_matched_apartments(f, look_back)
    count = len(results)
    return HttpResponse(simplejson.dumps({'count': count, 'scanned': scanned}),
                        mimetype="application/json")
