import datetime

from google.appengine.api import memcache
from appengine_django.models import BaseModel
from google.appengine.ext import db


__all__ = ('Apartment','ApartmentCounts')

class ApartmentCounts(BaseModel):
    updated = db.DateTimeProperty()
    propertyname = db.StringProperty()
    propertyvalue = db.StringProperty()
    count = db.IntegerProperty()

    @classmethod
    def delete_all(cls):
        N = 40
        rpc = db.create_rpc(deadline=30, read_policy=db.EVENTUAL_CONSISTENCY)
        q = db.GqlQuery("SELECT __key__ FROM ApartmentCounts",
                        rpc=rpc)
        for i in range(25):
            results = q.fetch(N)
            c = len(results)
            db.delete(results)
            if c < N:
                break


    @classmethod
    def update_data(cls, count_data):
        cls.delete_all()
        now = datetime.datetime.now()
        for key, counts in count_data.items():
            key = key.split('__', 1)
            if len(key) < 2:
                continue
            field, value = key
            f = cls(updated=now,
                    propertyname=field,
                    propertyvalue=value,
                    count=counts)
            f.put()

    @classmethod
    def get_data_dict(cls):
        ckey = 'acdd'
        data = memcache.get(ckey)
        if data:
            return data

        query = cls.all()
        results = query.fetch(1000)
        data = {}
        for result in results:
            if result.propertyname not in data:
                data[result.propertyname] = {result.propertyvalue: result.count}
            else:
                data[result.propertyname][result.propertyvalue] = result.count

        if data:
            memcache.set(ckey, data, 3600 * 16)
        return data

class Apartment(BaseModel):
    url = db.LinkProperty(required=True)
    id = db.IntegerProperty(required=True)
    updated = db.DateTimeProperty()
    updated_hour = db.IntegerProperty()
    updated_day = db.IntegerProperty()
    region = db.StringProperty()

    location = db.GeoPtProperty()
    location_accuracy = db.StringProperty()
    geohash = db.StringProperty()
    addr = db.StringProperty()

    concierge = db.BooleanProperty()
    washerdryer = db.BooleanProperty()
    hotwater = db.BooleanProperty()
    heat = db.BooleanProperty()
    brokerfee = db.BooleanProperty()
    cats = db.BooleanProperty()

    price = db.FloatProperty()
    price_thousands = db.IntegerProperty()

    size = db.StringProperty()

    def put(self, *args, **kwargs):
        self.updated_hour = int(self.updated.strftime("%Y%m%d%H"))
        self.updated_day = int(self.updated.strftime("%Y%m%d"))
        if self.price:
            self.price_thousands = int(self.price) / 1000 * 1000
        return super(Apartment, self).put(*args, **kwargs)

    def __str__(self):
        return '<Apartment %s: %r>' % (self.id,
                                       self.url)

    __repr__ = __str__

    @classmethod
    def delete_some(cls, num=10, N=30):
        read_back = 3
        rpc = db.create_rpc(deadline=30, read_policy=db.EVENTUAL_CONSISTENCY)
        q = db.GqlQuery("SELECT __key__ FROM Apartment WHERE updated < :1",
                        datetime.datetime.now() - datetime.timedelta(days=read_back),
                        rpc=rpc)
        results = q.fetch(N)
        quotient, mod = divmod(num, N)
        quotient += 1
        deleted = 0
        for i in range(quotient):
            results = q.fetch(N)
            c = len(results)
            if i == (quotient - 1):
                results = results[:mod]
            deleted += len(results)
            db.delete(results)
            if c < N:
                break
        return deleted
