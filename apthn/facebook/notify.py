import time

from django.conf import settings
from facebook import Facebook


def send_fb_notifications(aptf, results):
    fb = Facebook(settings.FACEBOOK_API_KEY, settings.FACEBOOK_SECRET_KEY)
    uid = int(aptf.get_email()[3:])
    r = fb.dashboard.setCount(uid, int(time.time()))
    r = fb.dashboard.addNews(uid,
                             [{'message': 'Test!',
                               'action_link': {'href': 'http://cnn.com',
                                               'text': 'boo'},}])
    r = fb.notifications.sendEmail([uid],
                                   "Test!",
                                   "This is another test",
                                   '')
    raise Exception(r)
