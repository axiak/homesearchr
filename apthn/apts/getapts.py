#!/usr/bin/env python
import re
import time
import urllib
import datetime
import traceback
import sys
import os

from google.appengine.ext import db
from google.appengine.api import urlfetch
from google.appengine.api import memcache

from django.conf import settings
from django.http import HttpResponse

from apthn.utils import geohash

from apthn.apts.models import *
from apthn.apts.zoneinfo import *
from apthn.filters.analyzers import analyzers, FailTryAgain

cg_id_re = re.compile(r'(\d+)\.html')
cltag_re = re.compile(r'CLTAG\s+([^=\s]+)=(.*?)-->')

results = []

def getapts(request, city):
    LIMIT = int(request.GET.get("LIMIT", 20))
    HLIMIT = int(request.GET.get("HLIMIT", LIMIT)) * 3
    results = []
    if city.lower() not in settings.CITIES:
        return HttpResponse("City %s not found." % city)

    city = (city.lower(), settings.CITIES[city.lower()])

    HLIMIT = max(HLIMIT, LIMIT)

    upper_range = HLIMIT / 100 + 1

    num_parsed = 0
    dtime = qtime = 0

    for idx, apturl in enumerate(get_all_apts(city, upper_range)):
        if idx > HLIMIT:
            break

        cgid = get_id(apturl)
        if not cgid:
            continue

        if num_parsed % 10 == 0 and num_parsed > 9:
            start = time.time()
            num_deleted = Apartment.delete_some(12)
            dtime += time.time() - start
            if settings.DEBUG:
                results.append("DELETED %s...." % num_deleted)

        start = time.time()
        aptfound = apartment_is_found(cgid)
        if settings.DEBUG:
            qtime += time.time() - start

        if aptfound:
            continue
        
        debug_info = analyze_url(city, apturl, cgid)
        results.append("Finished with %s" % cgid)
        if settings.DEBUG:
            results.append(str(debug_info))
        num_parsed += 1
        if num_parsed > LIMIT:
            break

    if num_parsed % 10:
        start = time.time()
        num_deleted = Apartment.delete_some(num_parsed % 10 + 1)
        dtime += time.time() - start
        if settings.DEBUG:
            results.append("DELETED %s...." % num_deleted)

    if settings.DEBUG:
        results.append("Query time took: %s" % qtime)
        results.append("Delete time took: %s" % dtime)

    return HttpResponse('\n'.join(results), mimetype='text/plain')


def apartment_is_found(cgid):
    rpc = db.create_rpc(deadline=18, read_policy=db.EVENTUAL_CONSISTENCY)
    ckey = "apt_f_%s" % cgid
    TIME = 3600 * 5
    r = memcache.get(ckey)
    if r is not None:
        return True
    apt = db.GqlQuery("SELECT * FROM Apartment "
                      "WHERE id = :1 LIMIT 1", cgid,
                      rpc=rpc).get()
    result = False
    if apt:
        if apt.location or apt.location_accuracy != "TRY_AGAIN":
            result = True

    memcache.set(ckey, result, TIME)
    return result

def getapt(request, city, cgid):
    """
    Get information for a specific craigslist id.
    """
    cgid_parts = cgid.rsplit('/', 1)
    if len(cgid_parts) > 1:
        index, cgid = cgid_parts
    else:
        index = ''
    cgid = long(cgid)
    apturl = 'http://%s.craigslist.org/%s/%s.html' % (city.lower(), index, cgid)
    debug_info = analyze_url(city, apturl, cgid)
    results.append("Finished with %s" % cgid)
    if settings.DEBUG:
        results.append(str(debug_info))
    return HttpResponse('\n'.join(results), mimetype='text/plain')


def analyze_url(city, apturl, cgid):
    result = urlfetch.fetch(apturl)
    if result.status_code != 200:
        return
    html = result.content
    update_time = get_update_time(html)
    cltags = parse_cltags(html)

    kwargs = {
        'updated': update_time,
        }
    for analysis in analyzers.values():
        try:
            kwargs.update(analysis.analyze_content(cltags, html, apturl))
        except FailTryAgain, e:
            return "Trying later on, something failed"
        except int, e:
            traceback.print_exc()

    a = Apartment(key_name = str(cgid),
                  url = apturl,
                  id = cgid,
                  region = city.upper(),
                  **kwargs)
    a.put()
    if kwargs.get('location') or kwargs.get('location_accuracy') != 'TRY_AGAIN':
        memcache.set("apt_f_%s" % cgid, True, 3600 * 5)
    return str(kwargs)

_update_time_re = re.compile(r"Date:\s+(\d{4})\D(\d{1,2})\D(\d{1,2})\D{1,3}(\d{1,2}):(\d{1,2})(PM|AM)\D{1,2}(\w{3,6})", re.I)
def get_update_time(html):
    m = _update_time_re.search(html)
    if not m:
        # We don't have a date time to show, use now.
        return datetime.datetime.now()
    groups = m.groups()
    nums = map(int, list(groups[:-2]))
    ampm = groups[-2]
    tz = groups[-1]
    if ampm.upper() == 'PM':
        nums[3] += 12
    tzoffset = ZONES.get(tz, ZONES['UTC'])
    d = datetime.datetime(*nums) + tzoffset
    return d

def parse_cltags(html):
    cltags = {}
    html = html.split('<!-- START CLTAGS -->', 1)
    if len(html) < 2:
        return cltags
    html = html[1]
    for match in cltag_re.finditer(html):
        val = match.groups()[1].strip()
        val = val.decode('ascii', 'ignore').encode('ascii')
        cltags[match.groups()[0].lower()] = val.strip()
    return cltags


def get_id(url):
    m = cg_id_re.search(url)
    if m:
        return int(m.groups()[0])
    else:
        return None

def get_all_apts(city, pages=1):
    for i in range(pages):
        for apt in get_apts(city, i * 100):
            yield apt

def get_with_cache(url, cache_time=300):
    result = memcache.get('wc_' + url)
    if result:
        if result is 'NC':
            return ''
        else:
            return result

    result = urlfetch.fetch(url)
    if result.status_code == 200:
        content = result.content
    else:
        content = 'NC'

    memcache.set('wc_' + url, content, cache_time)
    return content


def get_apts(city, idx=''):
    url = 'http://%s.craigslist.org/%s/index%s.html' % (city[0],
                                                        city[1],
                                                        idx or '')
    links_re = links_re = re.compile(r'href="(http://%s.craigslist[^"]+\.html)'
                                     % city[0])
    result = get_with_cache(url)
    if result:
        matches = list(links_re.finditer(result))
        matches.reverse()
        return [x.groups()[0] for x in matches]
    else:
        return ()

if __name__ == '__main__':
    main()
