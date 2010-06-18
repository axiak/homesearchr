import re
import math
import urllib
import logging
from django.utils import simplejson
from django.conf import settings

from google.appengine.ext import db
from google.appengine.api import urlfetch

from apthn.utils.geocode.geocode import geocode

from apthn.utils import geohash

__all__ = ('analyzers','FailTryAgain','NoFiltering',)

googm_re = re.compile(r'http://maps.google.com/\?q=([^"&]+)')
price_re = re.compile(r'\$([,\d]{3,5})')
_remove_tags = re.compile(r'<[^>]+>')

# Heat and hot water...
_hwre = re.compile(r'\W(?:heat|ht)\s*(?:and|&|&amp;)\s*(?:hw|hot\s+water)\s+incl', re.I)
_hwre2 = re.compile(r'utilities:?\W+(?:heat|ht)\W{1,4}(and)?\W{0,4}(?:hw|hot\s+water)', re.I)
_hw1 = re.compile(r'\Winclude:?\W{1,10}(?:hw|hot\s+water)\W', re.I)
_hw2 = re.compile(r'\W(?:hw|hot\s+water)\W{1,10}includ', re.I)
_ht1 = re.compile(r'\Winclude:?\W{1,10}(?:ht|heat)\W', re.I)
_ht2 = re.compile(r'\W(?:ht|heat)\W{1,10}includ', re.I)
_ld1 = re.compile(r'\Wlaundry\W{1,10}(?:room|unit)', re.I)
_ld2 = re.compile(r'\Wwasher\s?(?:/|and)\s?dryer\W{1,10}(?:room|unit)', re.I)

class FailTryAgain(Exception):
    pass

NoFiltering = object()

class Analyzers(object):
    library = {}
    def register(self, name, obj=None):
        if obj is None and not isinstance(name, basestring):
            obj = name
            name = obj.__class__.__name__.lower()
        self.library[name] = obj
    def items(self):
        return self.library.items()
    def values(self):
        return self.library.values()
    def __iter__(self):
        for i in self.library.values():
            yield i

analyzers = Analyzers()

class Analyzer(object):
    name = None
    run_multi = True
    def analyze_content(self, cltags, html):
        raise NotImplementedError("Not implemented")

    def update_apt_query(self, aptf, q, debug_info):
        raise NotImplementedError("Not implemented")

    def create_weight(self, aptf, apartment):
        raise NotImplementedError("Not implemented")

    def filter_size_estimate(self, apt_breakdown, aptf):
        raise NotImplementedError("Not implemented")

    def _linearize(self, value, lower, upper):
        return min(max((value - lower)/(upper - lower), 0), 1)


class BooleanProperty(Analyzer):
    run_multi = False
    name = ''
    def update_apt_query(self, aptf, q, debug_info):
        val = getattr(aptf, self.name)
        if val >= 0:
            q.filter("%s =" % self.name, bool(val))
            debug_info.append(("%s =" % self.name, bool(val)))
            return True

    def create_weight(self, aptf, apartment):
        val1 = getattr(aptf, self.name)
        val2 = getattr(apartment, self.name)
        if val1 < 0:
            return 1
        return 1 - int(val1 ^ val2)

    def filter_size_estimate(self, apt_breakdown, aptf):
        value = getattr(aptf, self.name)
        if value < 0:
            return NoFiltering
        value = unicode(bool(value))
        if self.name not in apt_breakdown:
            return NoFiltering
        return apt_breakdown[self.name].get(value, NoFiltering)

class Price(Analyzer):
    name = 'price_thousands'
    def analyze_content(self, cltags, html, url):
        m = price_re.search(html)
        if m:
            return {'price': float(m.groups()[0].replace(',', ''))}
        else:
            return {}

    def update_apt_query(self, aptf, q, debug_info):
        upper = aptf.price[1]
        prices = []
        for i in range(int(upper) / 1000 + 1):
            prices.append(i * 1000)
        q.filter("price_thousands IN", prices)
        debug_info.append(("price_thousands IN", prices))
        #q.filter("price <=", aptf.price[1])

    def create_weight(self, aptf, apartment):
        if not apartment.price:
            return 0
        return self._linearize(apartment.price,
                               aptf.price[1],
                               aptf.price[0])

    def filter_size_estimate(self, apt_breakdown, aptf):
        if 'price' not in apt_breakdown:
            return NoFiltering
        upper = aptf.price[1]
        total = 0
        if upper > 3999:
            return NoFiltering
        for i in range(int(upper) / 1000):
            val = u'%d' % (i * 1000)
            total += apt_breakdown['price'].get(val, 0)
        return total

analyzers.register(Price())

class Cats(BooleanProperty):
    name = 'cats'
    def analyze_content(self, cltags, html, url):
        if cltags.get('catsareok', 'off') == 'on':
            return {'cats': True}
        else:
            return {'cats': False}
analyzers.register(Cats())

class Concierge(BooleanProperty):
    name = 'concierge'
    def analyze_content(self, cltags, html, url):
        if 'concierge' in html.lower():
            return {'concierge': True}
        else:
            return {'concierge': False}
analyzers.register(Concierge())

class WasherDryer(BooleanProperty):
    name = 'washerdryer'
    def analyze_content(self, cltags, html, url):
        html = _remove_tags.sub(' ', html).replace(' in ', ' ').replace(' the ', ' ')
        if any(x.search(html) for x in (_ld1, _ld2)):
            return {'washerdryer': True}
        else:
            return {'washerdryer': False}
analyzers.register(WasherDryer())

class Heat(BooleanProperty):
    name = 'heat'
    def analyze_content(self, cltags, html, url):
        html = _remove_tags.sub(' ', html)
        if any(x.search(html) for x in (_hwre, _hwre2, _ht1, _ht2)):
            return {'heat': True}
        else:
            return {'heat': False}
analyzers.register(Heat())


class HotWater(BooleanProperty):
    name = 'hotwater'
    def analyze_content(self, cltags, html, url):
        html = _remove_tags.sub(' ', html)
        if any(x.search(html) for x in (_hwre, _hwre2, _hw1, _hw2)):
            return {'hotwater': True}
        else:
            return {'hotwater': False}
analyzers.register(HotWater())


class BrokerFee(BooleanProperty):
    name = 'brokerfee'
    def analyze_content(self, cltags, html, url):
        piece = url.split('/')[-2]
        if piece == 'fee':
            return {'brokerfee': True}
        else:
            return {'brokerfee': False}
analyzers.register(BrokerFee())



class Size(Analyzer):
    name = 'size'
    def analyze_content(self, cltags, html, url):
        html = html.lower()
        size = None
        if 'studio' in html:
            size = 'studio'
        elif '1br' in html:
            size = '1br'
        elif '2br' in html:
            size = '2br'
        elif '3br' in html:
            size = '3br'
        elif '4br' in html:
            size = '4br'
        elif '5br' in html:
            size = '5br'
        elif '6br' in html:
            size = '6br'
        elif '7br' in html:
            size = '7br'
        elif '8br' in html:
            size = '8br'
        if size:
            return {'size': size}
        else:
            return {}
    def update_apt_query(self, aptf, q, debug_info):
        if aptf.size_names:
            val = [x.lower() for x in aptf.size_names]
            q.filter("size IN", val)
            debug_info.append(("size IN", val))

    def create_weight(self, aptf, apartment):
        return 1

    def filter_size_estimate(self, apt_breakdown, aptf):
        if 'size' not in apt_breakdown:
            return NoFiltering
        data = apt_breakdown['size']
        total = 0
        for size in aptf.size_names:
            total += data.get(size.lower(), 0)
        return total

analyzers.register('size', Size())


class Location(Analyzer):
    name = 'geohash'
    def analyze_content(self, cltags, html, url):
        results = {}
        match = googm_re.search(html)
        city = url[7:].split('.', 1)[0]
        locstring = settings.CITY_LOC[city.lower()]
        if match:
            addr = urllib.unquote_plus(match.groups()[0])
            addr = addr.replace('loc:', '').strip()
            results['location_accuracy'] = 'MAPS_URL'
        elif 'xstreet0' in cltags:
            addr = '%s & %s, %s, %s' % (cltags['xstreet0'], cltags['xstreet1'], cltags['city'], cltags['region'])
            results['location_accuracy'] = 'XSTREET'
        elif 'geographicarea' in cltags:
            addr = '%s, %s' % (cltags['geographicarea'], locstring)
            results['location_accuracy'] = 'AREA'
        else:
            results['location_accuracy'] = 'NONE'
            results['addr'] = 'N/A'
            return results

        results['addr'] = addr.encode('utf8', 'ignore')

        try:
            results.update(geocode(addr))
        except FailTryAgain:
            return {'location_accuracy': 'TRY_AGAIN'}
        results['geohash'] = None

        if results.get('location'):
            ll = results.get('location')
            results['geohash'] = str(geohash.Geohash((ll.lon, ll.lat)))

        return results


    def update_apt_query(self, aptf, q, debug_info):
        if not aptf.polygons:
            return self.circles_update_apt_query(aptf, q, debug_info)
        min_lat, max_lat, min_lon, max_lon = 1000, -1000, 1000, -1000

        for polygon in aptf.nice_polygons:
            for lat, lon in polygon:
                if lat < min_lat:
                    min_lat = lat
                elif lat > max_lat:
                    max_lat = lat
                if lon < min_lon:
                    min_lon = lon
                elif lon > max_lon:
                    max_lon = lon

        val1 = str(geohash.Geohash((min_lon, min_lat)))
        val2 = str(geohash.Geohash((max_lon, max_lat)))
        q.filter("geohash >=", val1)
        q.filter("geohash <=", val2)
        debug_info.append(("geohash >=", val1))
        debug_info.append(("geohash <=", val2))


    def circles_update_apt_query(self, aptf, q, debug_info):
        min_lat, max_lat, min_lon, max_lon = 1000, -1000, 1000, -1000

        # 0.014457066996884592 = 180 / (2 * pi * radius of earth)

        # Create a bounding box..
        for i, center in enumerate(aptf.distance_centers):
            upper = aptf.distances[2 * i + 1]
            upper = 0.014457066996884592 * upper
            ca, co = center.lat, center.lon
            if ca - upper < min_lat:
                min_lat = ca - upper
            if ca + upper > max_lat:
                max_lat = ca + upper
            if co - upper < min_lon:
                min_lon = co - upper
            if co + upper > max_lon:
                max_lon = co + upper

        val1 = str(geohash.Geohash((min_lat, min_lon)))
        val2 = str(geohash.Geohash((max_lat, max_lon)))
        q.filter("geohash >=", val1)
        q.filter("geohash <=", val2)
        debug_info.append(("geohash >=", val1))
        debug_info.append(("geohash <=", val2))

    def create_weight(self, aptf, apartment):
        if not aptf.polygons:
            return self.circles_create_weight(aptf, apartment)
        if not apartment.location:
            return 0
        alat, alon = apartment.location.lat, apartment.location.lon
        for polygon in aptf.nice_polygons:
            if self._pnt_in_poly(polygon, (alat, alon)):
                return 1
        return 0

    def circles_create_weight(self, aptf, apartment):
        if not apartment.location:
            return 0
        alat, alon = apartment.location.lat, apartment.location.lon

        max_distance_score = 0
        for i, center in enumerate(aptf.distance_centers):
            lower, upper = aptf.distances[2 * i], aptf.distances[2 * i + 1]
            distance = self._gcdistance(center.lat, center.lon,
                                        alat, alon)
            distance_score = self._linearize(distance, upper, lower)
            if distance_score > max_distance_score:
                max_distance_score = distance_score
        return max_distance_score ** 2

    def _pnt_in_poly(self, polygon, point):
        # Check to see if a point is in polygon
        # Ref: http://www.ariel.com.au/a/python-point-int-poly.html
        n = len(polygon)
        inside = False

        x, y = point
        p1x, p1y = polygon[0]
        for i in range(n+1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y

        return inside

    def _gcdistance(self, lat1, lon1, lat2, lon2):
        f = math.radians
        lat1, lon1, lat2, lon2 = map(f, (lat1, lon1, lat2, lon2))

        dlong = lon2 - lon1
        dlat = lat2 - lat1

        a = math.sin(dlat / 2.0)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlong / 2.0)**2
        c = 2 * math.asin(min(1, math.sqrt(a)))
        return 3956 * c

    def filter_size_estimate(self, apt_breakdown, aptf):
        return -1

analyzers.register('Location', Location())
