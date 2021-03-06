import re
import urllib
import random
from django.utils import simplejson
from django.conf import settings

from google.appengine.ext import db
from google.appengine.api import urlfetch

from apthn.utils.geocode.models import GeoCodeCache

__all__ = ('geocode',)

entity_re = re.compile(r'\&#?\w{3,5};')
nonword_re = re.compile(r'[^,\w]')
space_re = re.compile(r'\s+')
lat_re = re.compile(r'<Latitude>(.+?)</Latitude>')
long_re = re.compile(r'<Longitude>(.+?)</Longitude>')

def _clean_addr(addr):
    addr = entity_re.sub('', addr)
    addr = nonword_re.sub(' ', addr)
    return space_re.sub(' ', addr).lower().strip()

def geocode_google(addr):
    from apthn.filters.analyzers import FailTryAgain
    url = 'http://maps.google.com/maps/api/geocode/json?address=%s&sensor=false' % urllib.quote(addr)
    result = urlfetch.fetch(url)
    if result.status_code != 200:
        raise ValueError("Could not download: %r" % url)

    json = result.content
    data = simplejson.loads(json)

    try:
        latlong = data['results'][0]['geometry']['location']
        return (latlong['lat'], latlong['lng'])
    except (KeyError, IndexError):
        if data.get('status') == 'OVER_QUERY_LIMIT':
            raise FailTryAgain()
        else:
            raise ValueError("Fail: %s" % data.get('status'))


def geocode_yahoo(addr):
    from apthn.filters.analyzers import FailTryAgain
    q = urllib.quote
    url = 'http://local.yahooapis.com/MapsService/V1/geocode?appid=%s&location=%s' % (q(settings.YAHOO_APPID), q(addr))
    result = urlfetch.fetch(url)
    if result.status_code != 200:
        raise ValueError("Could not download: %r" % url)
    xml = result.content
    if 'LIMIT EXCEEDED' in xml:
        raise FailTryAgain()
    m = lat_re.search(xml)
    lat, lng = None, None
    if m:
        try:
            lat = float(m.groups()[0])
        except:
            pass
    m = long_re.search(xml)
    if m:
        try:
            lng = float(m.groups()[0])
        except:
            pass
    if lat is None or lng is None:
        raise ValueError("Coult not get lat/lng yahoo")
    return lat, lng

geocoders = [geocode_google, geocode_yahoo]

def geocode(addr):
    from apthn.filters.analyzers import FailTryAgain
    results = {}
    addr = _clean_addr(addr)

    result = GeoCodeCache.all().filter("addr =", addr).get()
    if result:
        return {'location': result.location}

    try_again = False
    errors = []
    random.shuffle(geocoders)
    for coder in geocoders:
        try:
            location = db.GeoPt(*coder(addr))
        except FailTryAgain, e:
            try_again = True
            continue
        except Exception, e:
            errors.append(e.message)
            continue
        result = GeoCodeCache(key_name=addr,
                              addr=addr,
                              location=location)
        result.put()
        return {'location': location}

    if try_again:
        raise FailTryAgain("At least one of them had a quote issue?")
    return {'location': None,
            'location_accuracy': ('::'.join(errors))[:500]}
