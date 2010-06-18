from google.appengine.api import users
from google.appengine.ext import db

class AppEngineAuthMiddleware(object):
    def process_request(self, request):
        request.user = users.get_current_user()

class AuthenticationMiddleware(object):
    def process_request(self, request):
        def getuser(request):
            if not request.COOKIES.has_key("sessioncookie"):
                return None
            if hasattr(request, "_cached_user"):
                if request.realuser == None:
                    return None
                return request.realuser
            hunters = db.GqlQuery("SELECT * FROM AptHunter WHERE SESSIONCOOKIE = :1", request.COOKIES["sessioncookie"])
            if hunters.count(1) > 0:
                request._cached_user = hunters[0]
                return hunters[0]
            request.cached_user = None
            return None
        
        if not hasattr(request.__class__, "user"):
            request.__class__.user = property(getuser)
