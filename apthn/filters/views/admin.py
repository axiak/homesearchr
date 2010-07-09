import re
import os
import sys
import string
import logging
import random
import datetime
import traceback

from django.utils import simplejson
from django.views.generic.simple import direct_to_template
from django.http import HttpResponse

from apthn.apts.models import *
from apthn.filters.models import *
from apthn.users.models import *

from apthn.filters.views import email

from apthn.facebook.notify import send_fb_notifications

def filter_view(request):
    filters = []
    N = 500

    query = AptFilter.all().filter("expires >", datetime.date.today())
    query.filter("active =", True)

    seen_emails = set()

    while True:
        results = query.fetch(N)
        
        for aptf in results:
            email = aptf.get_email()
            if email not in seen_emails:
                filters.append(aptf)
        if len(results) < N:
            break
    results.sort(key=lambda x: x._created, reverse=True)
    #return HttpResponse('\n'.join("%s: %s" % (k, v) for k, v in results[0].__dict__.items()))
    return direct_to_template(request, 'admin/viewfilters.html',
                              {'filters': filters})

def filter_info(request, id_value):
    try:
        aptf = AptFilter.get_by_id(int(id_value))
    except ValueError:
        aptf = AptFilter.get_by_key(id_value)
    if aptf:
        results = email.get_matched_apartments(aptf)
        results[0].sort(key=lambda x: x[0], reverse=True)

    else:
        results = None

    return direct_to_template(request, 'admin/inspectfilter.html',
                              {'filter': aptf,
                               'results': results})
    
