import datetime, hashlib

from google.appengine.api import mail
from google.appengine.ext import db

from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.views.generic.simple import direct_to_template
from django import forms

from models import AptHunter

def login(request):
    r = request.POST
    if not (r.has_key("username") and r.has_key("password")):
        #this can be eliminated by making a LoginForm
        return HttpResponseRedirect("/")
    hunter = AptHunter.login(r["username"],r["password"])
    response = HttpResponseRedirect("/filters/create/%s/"%hunter.last_city)
    response.set_cookie("sessioncookie", hunter.sessioncookie)
    response.set_cookie("username", hunter.username)
    return response

def forgot(request):
    if not request.REQUEST.has_key("email"):
        return direct_to_template(request, "forgotlogin.html")
    hunters = db.GqlQuery("SELECT * FROM AptHunter WHERE email = :1", request.REQUEST["email"])
    if hunters.count(1) < 1:
        return direct_to_template(request, "forgotlogin.html", extra_context={"email":request.REQUEST["email"]})
    hunter = hunters[0]
    msg = mail.EmailMessage(sender=settings.FROM_EMAIL,
                            to=hunter.email,
                            subject="Homesearchr login reset",
                            bcc=settings.ADMINS[0][1],
                            )
    # it should be easy enough to predict this reset cookie
    h = hashlib.sha1()
    h.update(hunter.username)
    h.update(str(datetime.datetime.now))
    h.update("supar sekrit tel no1")
    resetcookie = h.hexdigest() + "reset"
    hunter.sessioncookie = resetcookie
    db.put(hunter)
    msg.body = "Please use an HTML compatible email program to see this."
    msg.html = '<a href="http://homesearchr.com/users/reset?reset=%s">Click here to reset your homesearcher login</a>'%resetcookie
    msg.send()
    return direct_to_template(request, "forgotlogin-success.html", extra_context={"email":hunter.email})

def reset(request):
    code = request.GET.get('reset')
    if code[-5:] != "reset":
        return direct_to_template(request, template="forgotlogin.html", extra_context={"invalid_reset_code": True})
    hunters = db.GqlQuery("SELECT * FROM AptHunter WHERE sessioncookie = :1", code)
    if len(hunters) < 1:
        return direct_to_template(request, template="forgotlogin.html", extra_context={"invalid_reset_code": True})
    hunter = hunters[0]
    resetform = forms.ResetForm(initial={"username":hunter.username})
    return direct_to_template(request, "resetlogin.html", {'resetform':resetform})
