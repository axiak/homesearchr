from google.appengine.ext import db

__all__ = ('AptHunter',)

class AptHunter(db.Model):
    user = db.UserProperty()
    email = db.EmailProperty()
    contactinfo = db.StringProperty(required=True)
    first_created = db.DateTimeProperty()

    def __str__(self):
        return '<User %s>' % contactinfo

    __repr__ = __str__
