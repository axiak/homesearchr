from google.appengine.api import users
from google.appengine.ext import db

class AppEngineAuthMiddleware(object):
    def process_request(self, request):
        request.user = users.get_current_user()

class authentication_middleware(object):
    def process_request(self, request):
        def makeuser(request):
            if request.COOKIES.has_key("sessioncookie"):
                hunters = db.GqlQuery("SELECT * FROM AptHunter WHERE SESSIONCOOKIE = :1", request.COOKIES["sessioncookie"])
                if len(hunters) > 0:
                    request.user = hunters[0]
            return request.user
        
        if not hasattr(request.__class__, "user"):
            request.__class__.user = property(makeuser)
        

    
