#!/usr/bin/env python
import re
import os
import sys
import string
import logging
import random
import datetime
import traceback

from django.utils import simplejson

from google.appengine.ext import db
from google.appengine.api import mail
from google.appengine.api.labs import taskqueue

from apthn.apts.models import *
from apthn.filters.models import *
from apthn.users.models import *

from apthn.filters.analyzers import analyzers, NoFiltering

from apthn.facebook.notify import send_fb_notifications

from django.conf import settings
from django.http import HttpResponse

from apthn.utils.randstr import randstr


YESTERDAY = datetime.datetime.today() - datetime.timedelta(days=1)
NOW = datetime.datetime.now()

__all__ = ('send_emails', 'perform_notify', 'get_matched_apartments',
           'enqueue_notify', 'send_one_email')

def send_emails(request):
    email = request.GET.get("email")
    admin = bool(int(request.GET.get('admin', 0)))

    if email:
        try:
            emails = simplejson.loads(email.decode('base64'))
        except:
            emails = [email]
    else:
        emails = AptFilter.get_all_emails()

    for email in emails:
        enqueue_notify(email, admin)

    return HttpResponse("enqueued: %s\n" % '\n'.join(emails),
                        mimetype="text/plain")

def enqueue_notify(email, admin=False):
    clean_email = email.encode('base64').rstrip().rstrip('=')
    taskqueue.add(url="/filters/email/one/",
                  params={"email": email, "admin": str(int(admin))},
                  name="Notify-%s-%s" % (clean_email,
                                         randstr()),
                  method="GET")

def send_one_email(request):
    email = request.GET['email']
    admin = bool(int(request.GET.get('admin', 0)))

    hunter = AptHunter.all().filter("contactinfo =", email).get()
    if not hunter:
        raise ValueError("Could not find hunter %s" % hunter)

    query = AptFilter.all().filter("apth =", hunter)
    query.filter("expires >", datetime.date.today())
    query.filter("active =", True)

    result = query.get()
    if not result:
        raise ValueError("Could not find filter for %s" % hunter)

    perform_notify(result, admin)

    return HttpResponse("Sent to %s (admin: %s)" % (result, admin),
                        mimetype="text/plain")


def perform_notify(aptf, admin_send=False):
    results, total_scanned = get_matched_apartments(aptf)[:2]
    results.sort(reverse=True)
    aptf.disable_string = ''.join(random.choice(string.letters)
                                  for x in xrange(32))

    try:
        cinfo = str(aptf.get_email())
    except ValueError:
        return

    if results:
        if cinfo.startswith('fb-'):
            send_fb_notifications(aptf, results)
        else:
            send_email(aptf, results, admin_send)

    aptf.last_notified = NOW
    aptf.put()


def debug_print_info(filter_strings):
    pieces = ['Apartment.all()']
    for name, val in filter_strings:
        pieces.append(r'filter("%s", %r)' % (name, val))
    return '.'.join(pieces)

def get_matched_apartments(aptf, updated_since=YESTERDAY):
    rpc = db.create_rpc(deadline=18, read_policy=db.EVENTUAL_CONSISTENCY)
    q = Apartment.all()

    filter_strings = []

    if not aptf.region:
        region = 'BOSTON'
    else:
        region = aptf.region

    q.filter("region =", region)
    filter_strings.append(("region =", region))

    d = datetime.datetime.now()
    dates = []
    while d > updated_since:
        dates.append(int(d.strftime("%Y%m%d")))
        d -= datetime.timedelta(days=1)


    if len(dates) <= 5:
        q.filter("updated_day IN", dates)
        filter_strings.append(("updated_day IN", dates))


    breakdown_data = ApartmentCounts.get_data_dict()

    filter_estimates = []
    for analyzer in analyzers:
        val = analyzer.filter_size_estimate(breakdown_data, aptf)
        if val != NoFiltering:
            filter_estimates.append((val, analyzer))

    filter_estimates.sort()

    i = 0

    applied = []

    for score, analyzer in filter_estimates:
        analyzer.update_apt_query(aptf, q, filter_strings)
        applied.append(analyzer)
        i += 1
        if i > 2:
            break

    results = []
    total_scanned = 0

    logging.info(debug_print_info(filter_strings))

    while True:
        curresults = q.fetch(750, rpc=rpc)
        for apartment in curresults:
            if apartment.updated < updated_since:
                continue
            scores = {}
            total = 1
            for analyzer in analyzers:
                score = analyzer.create_weight(aptf, apartment)
                scores[analyzer.__class__.__name__] = score
                total *= score
            if total > 0.1:
                results.append((total, scores, apartment))
        total_scanned += len(curresults)
        #if len(curresults) < 1000 or total_scanned > 3000:
        break
        #rpc = db.create_rpc(deadline=18, read_policy=db.EVENTUAL_CONSISTENCY)
    return (results, total_scanned, debug_print_info(filter_strings))

def send_email(aptf, results, admin_send=False):
    from django.template.loader import render_to_string
    from django.conf import settings

    if admin_send:
        to_email = settings.ADMINS[0][1]
    else:
        to_email = aptf.get_email()

    html=render_to_string("email.html", {'results': results[:25],
                                         'user': aptf.apth,
                                         'disable': aptf.disable_string})
    msg = mail.EmailMessage(sender=settings.FROM_EMAIL,
                            to=to_email,
                            subject=settings.EMAIL_SUBJECT,
                            bcc=settings.ADMINS[0][1],
                            )
    msg.body = "Please use an HTML compatible email program to see this."
    msg.html = html

    msg.send()
