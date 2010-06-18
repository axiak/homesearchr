import datetime,hashlib

from google.appengine.ext import db

__all__ = ('AptHunter',)

class AptHunter(db.Model):
    user = db.UserProperty() #something unique
    email = db.EmailProperty() # email address
    contactinfo = db.StringProperty(required=True) #what does this do
    first_created = db.DateTimeProperty(auto_now_add=True)
    username = db.StringProperty()
    password = db.StringProperty()
    last_city = db.StringProperty() #where they were last
    sessioncookie = db.StringProperty() #random number

    def __str__(self):
        return '<User %s>' % contactinfo

    __repr__ = __str__

    def hash_password(user, password):
        h = hashlib.sha1()
        h.update(str(user.first_created))
        h.update(password)
        return h.hexdigest()        

    # in order to calculate the user's session cookie, need to know
    # when they logged in.  with usec.
    def generate_sessioncookie(user):
        h = hashlib.sha1()
        h.update(user.username)
        h.update(str(datetime.datetime.now()))
        sessioncookie = h.hexdigest()
        user.sessioncookie = sessioncookie
        db.put(user)
        return sessioncookie

    @classmethod
    def login(lol, username, password):
        hunters = db.GqlQuery("SELECT * FROM AptHunter WHERE username = :1", username)
        hunter = hunters[0]
        if hunter.password != hunter.hash_password(password):
            return None
        hunter.generate_sessioncookie()
        return hunter

    @classmethod
    def name_available(lol, username):
        hunters = db.GqlQuery("SELECT * FROM AptHunter WHERE username = :1", username)
        if hunters.count(1) > 0:
            return False
        return True
        
    @classmethod
    def make_user(thisclass, contactform):
        username    = contactform.cleaned_data["username"]
        email       = contactform.cleaned_data["email"]
        hunters = db.GqlQuery("SELECT * FROM AptHunter WHERE email = :1", email)
        if hunters.count(1) > 0:
            user = hunters[1]
            user.username = username
        else:
            user = thisclass(username =    username,
                             email =       email,
                             contactinfo = email)
        user.password = user.hash_password(contactform.cleaned_data["password"])
        user.generate_sessioncookie()
        db.put(user)
        return user
