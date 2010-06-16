from google.appengine.ext import db
from google.appengine.api.labs import taskqueue
from google.appengine.api import mail

from django.http import HttpResponse
from django.utils import simplejson

from apthn.utils import caching
from apthn.apts.models import Apartment, ApartmentCounts

from collections import defaultdict

import datetime
import time
import math

import pprint

try:
    import cPickle as pickle
except ImportError:
    import pickle

from apthn.utils.randstr import randstr


# Create your views here.
def clean_apts(request):
    NUM = int(request.GET.get('NUM', 300))
    COUNT = int(request.GET.get('COUNT', 0))
    SPAWN = int(request.GET.get('SPAWN', 0))
    nospawn = int(request.GET.get('CHILD', 0))

    if SPAWN:
        for i in range(int(math.ceil(NUM / 100.0))):
            COUNT = i * 100
            taskqueue.add(url="/apts/clean/", params={"NUM": NUM, "COUNT": COUNT, 'CHILD': '1'},
                          name="DELETE-%s-%s-spawn-%s" % (NUM, COUNT, randstr()),
                          method="GET")
        return HttpResponse("Spawned a lot of processes...", mimetype="text/plain")

    start = time.time()
    try:
        num_deleted = Apartment.delete_some(100, 30)
    except Exception, e:
        result = "Error: %s" % e
    else:
        result = "Num deleted: %s" % num_deleted
    total = time.time() - start
    result += "<br>Total Time: %0.3f sec" % total
    response = HttpResponse('<html><head><title>Deleting 100..</title><meta http-equiv="refresh" value="5"></head><body>Loading...<br>%s</body></html>' % result)

    COUNT += 100
    if not nospawn and COUNT < NUM:
        taskqueue.add(url="/apts/clean/", params={"NUM": NUM, "COUNT": COUNT},
                      name="DELETE-%s-%s-%s" % (NUM, COUNT, randstr()),
                      method="GET")

    return response

def count_apts(request):
    rpc = db.create_rpc(deadline=18, read_policy=db.EVENTUAL_CONSISTENCY)
    q = db.GqlQuery("SELECT __key__ FROM Apartment", rpc=rpc)
    N = 1000
    results = q.fetch(N)
    count = 0
    errors = ''
    try:
        while True:
            count += len(results)
            results = q.fetch(N)
            if len(results) < N:
                break
    except Exception, e:
        errors = str(e)
    return HttpResponse("Count: %s\n\n%s" % (count, errors),
                        mimetype="text/plain")


field_to_str = {
    'region': str,
    'concierge': str,
    'washerdryer': str,
    'hotwater': str,
    'heat': str,
    'brokerfee': str,
    'cats': str,
    'price': lambda x: str(int(x or 0) / 1000 * 1000),
    'size': str,
}

def count_breakdowns(request):
    INTERVAL = 200
    try:
        count_data = pickle.loads(request.POST['count_data'].decode('base64'))
    except:
        count_data = defaultdict(int)

    idx = int(request.POST.get('idx', 0))
    if idx == -1:
        ApartmentCounts.update_data(count_data)
        return HttpResponse("Boo", mimetype="text/plain")

    cursor = request.POST.get('cursor')

    query = Apartment.all().order("updated")
    if cursor:
        query.with_cursor(cursor)

    results = query.fetch(INTERVAL)

    for apt in results:
        for field, mapper in field_to_str.items():
            count_data['%s__%s' % (field, mapper(getattr(apt, field)))] += 1

    createstr = "Not creating"

    output = "%s\n\n%s" % (createstr, pprint.pformat(dict(count_data)))

    if len(results) == INTERVAL:
        idx += INTERVAL
        cursor = query.cursor()
        cdata = pickle.dumps(count_data).encode('base64')
        params = {'cursor': cursor, 'idx': idx, 'count_data': cdata}

        taskqueue.add(url="/apts/breakdown/", params=params,
                      name="Counter-%s-%s" % (idx, randstr()),
                      method="POST")

        createstr = "Spawning new process..."
    else:
        idx = -1
        cdata = pickle.dumps(count_data).encode('base64')
        params = {'idx': -1, 'count_data': cdata}
        taskqueue.add(url="/apts/breakdown/", params=params,
                      name="Counter-%s-%s" % (idx, randstr()),
                      method="POST")

    return HttpResponse(output, mimetype="text/plain")

@caching.cacheview(lambda request, city: 'aptlist_%s' % city.lower(), 7200)
def apt_list(request, city):
    limit = 4000
    query = Apartment.all()
    query.filter("region =", city.upper())
    query.order('-updated')
    bad_keys = ('price_thousands', 'region', 'updated_hour', 'updated_day',
                'addr', 'location_accuracy', 'geohash')

    results = []
    while True:
        queryresults = query.fetch(1000)
        if not queryresults:
            break
        for result in queryresults:
            d = dict(result._entity)
            for key in bad_keys:
                del d[key]
            d['updated'] = int(d['updated'].strftime("%s"))
            if d.get('location'):
                d['location'] = (d['location'].lat, d['location'].lon)
            else:
                continue
            results.append(d)
            if len(results) >= limit:
                break
        if len(results) >= limit:
            break

    return HttpResponse(simplejson.dumps({'results': results}),
                        mimetype='application/json')
