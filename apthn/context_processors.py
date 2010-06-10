from google.appengine.api import users

def auth(request):
    return {'LOGOUT_URL': users.create_logout_url(request.path),
            'USER': request.user}

def addreq(request):
    return {"REQUEST": request}
