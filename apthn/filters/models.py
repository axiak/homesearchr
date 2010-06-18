import datetime

from appengine_django.models import BaseModel
from google.appengine.ext import db

from apthn.users.models import AptHunter

__all__ = ('AptFilter',)

class AptFilter(BaseModel):
    user = db.UserProperty(required=False)
    apth = db.ReferenceProperty(AptHunter)
    created = db.DateProperty(auto_now_add=True)
    expires = db.DateProperty()
    active = db.BooleanProperty(default=True)
    last_notified = db.DateTimeProperty()

    region = db.StringProperty()

    disable_string = db.StringProperty()
    disable_status = db.StringProperty()

    distance_centers = db.ListProperty(db.GeoPt)
    distances = db.ListProperty(float)
    polygons = db.TextProperty()

    cats = db.IntegerProperty()
    concierge = db.IntegerProperty()
    washerdryer = db.IntegerProperty()
    heat = db.IntegerProperty()
    hotwater = db.IntegerProperty()
    brokerfee = db.IntegerProperty()

    price = db.ListProperty(int)

    size_names = db.StringListProperty()
    size_weights = db.ListProperty(float)

    @property
    def nice_polygons(self):
        if hasattr(self, '_nice_polygons'):
            return self._nice_polygons

        if not self.polygons:
            return []

        polygons = []
        polygon = []
        atoms = self.polygons.strip(',').split(',')
        atoms.append('p')
        for atom in atoms:
            if atom.lower() == 'p':
                polygon_collapse = [(polygon[i], polygon[i + 1])
                                    for i in range(0, len(polygon), 2)]
                if not polygon:
                    continue
                polygons.append(polygon_collapse)
                polygon = []
            else:
                polygon.append(float(atom))
        self._nice_polygons = polygons
        return polygons

    def get_email(self):
        if self.user:
            a = AptHunter.all().filter("user =", self.user).get()
            if not a:
                raise ValueError("BOO")
            return a.email
        else:
            if not self.apth:
                raise ValueError("BOO")

            if self.apth.email:
                return self.apth.email
            else:
                return self.apth.contactinfo

    def __str__(self):
        try:
            email = self.get_email()
        except ValueError:
            email = "N/A"
        return '<Filter %r, %s>' % (email, self.expires)

    @classmethod
    def get_all_emails(cls):
        emails = []
        N = 500

        query = AptFilter.all().filter("expires >", datetime.date.today())
        query.filter("active =", True)

        while True:
            results = query.fetch(N)
            emails.extend(aptf.get_email() for aptf in results
                          if aptf.good_to_email())
            if len(results) < N:
                break
        return emails


    def good_to_email(self):
        return (not self.last_notified) or \
            ((datetime.datetime.now() - self.last_notified) >= datetime.timedelta(days=1))
