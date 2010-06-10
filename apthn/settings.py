# Django settings for apthn project.
import os

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ("Michael Axiak", "mike@axiak.net"),
)

DEFAULT_FROM_EMAIL = "no-reply@homesearchr.com"

MANAGERS = ADMINS

TIME_ZONE = 'America/New_York'
SITE_ID = 1
USE_I18N = False

DATABASE_ENGINE = 'appengine'

MEDIA_ROOT = os.path.abspath(os.path.join(ROOT_DIR, '..', 'static'))

MEDIA_URL = '/static/'

DEBUG_IPS = ('127.0.0.1', '18.224.0.180','0.1.0.1',)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'tus7x+e!_^y#xm*)9c$hxcf48n@g%ee2g#8(8n#3%%=9@6kuqm'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'apthn.users.middleware.AppEngineAuthMiddleware',
    'facebook.djangofb.FacebookMiddleware',
    'apthn.errors.middleware.FixEmailsMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "apthn.context_processors.auth",
    "apthn.context_processors.addreq",
    "apthn.facebook.context_processors.facebook",
    )

ROOT_URLCONF = 'apthn.urls'

TEMPLATE_DIRS = (
    os.path.abspath(os.path.join(ROOT_DIR, '..', 'templates')),
)


INSTALLED_APPS = (
    'appengine_django',
    'django.contrib.sessions',
    'apthn.users',
    'apthn.apts',
    'apthn.filters',
)

GOOGLE_MAP_KEYS = {
    'apthuntnotifier.axiak.net': 'ABQIAAAAlhje1wiuAa0mocBP0cHQORRWUDg_CtXjZH51dYu3DjdIloAg7xQt4E6XQuvLb9eVmtnq7Z4FJ_pTLw',
    'apthuntnotifier.appspot.com': 'ABQIAAAAlhje1wiuAa0mocBP0cHQORRL5gSEOE3fMxQVCoEj-t1V_0eJkxTdT3xn_DgsfSir6pmCeX6-zaxryA',
    'localhost': 'ABQIAAAAlhje1wiuAa0mocBP0cHQORRL5gSEOE3fMxQVCoEj-t1V_0eJkxTdT3xn_DgsfSir6pmCeX6-zaxryA',
    'webapartmentquest.com': 'ABQIAAAAlhje1wiuAa0mocBP0cHQORSy9aAAzMwDkkXV2wUxZKH_3J-pkhRe2V2WoPaPYbfnZ7QdLAr0LLxZHg',
    'www.webapartmentquest.com': 'ABQIAAAAlhje1wiuAa0mocBP0cHQORTV85R_CYuy40wZywSnwSGcNZyPyRTIcjlkdLfEatbmThSy4mPKx6iUdg',
    'www.homesearchr.com': 'ABQIAAAAlhje1wiuAa0mocBP0cHQORSaMrK003P14Euu9-rjvh_L8wzhcxSa_M79DRYK3ikO_lkIGWS1RmIruA',
    'dev.homesearchr.com': 'ABQIAAAAlhje1wiuAa0mocBP0cHQORSX0tQptR9VZF7uIXA7I788z8hjABQg2147h9T8_eG_HWImXQmeJyAWnA',
}

GOOGLE_AJAX_KEYS = {
    'apthuntnotifier.axiak.net': 'ABQIAAAAlhje1wiuAa0mocBP0cHQORRWUDg_CtXjZH51dYu3DjdIloAg7xQt4E6XQuvLb9eVmtnq7Z4FJ_pTLw',
    'apthuntnotifier.appspot.com': 'ABQIAAAAlhje1wiuAa0mocBP0cHQORRL5gSEOE3fMxQVCoEj-t1V_0eJkxTdT3xn_DgsfSir6pmCeX6-zaxryA',
    'localhost': 'ABQIAAAAlhje1wiuAa0mocBP0cHQORRL5gSEOE3fMxQVCoEj-t1V_0eJkxTdT3xn_DgsfSir6pmCeX6-zaxryA',
    'webapartmentquest.com': 'ABQIAAAAlhje1wiuAa0mocBP0cHQORSy9aAAzMwDkkXV2wUxZKH_3J-pkhRe2V2WoPaPYbfnZ7QdLAr0LLxZHg',
    'www.webapartmentquest.com': 'ABQIAAAAlhje1wiuAa0mocBP0cHQORTV85R_CYuy40wZywSnwSGcNZyPyRTIcjlkdLfEatbmThSy4mPKx6iUdg',
    'www.homesearchr.com': 'ABQIAAAAlhje1wiuAa0mocBP0cHQORSaMrK003P14Euu9-rjvh_L8wzhcxSa_M79DRYK3ikO_lkIGWS1RmIruA',
    'dev.homesearchr.com': 'ABQIAAAAlhje1wiuAa0mocBP0cHQORSX0tQptR9VZF7uIXA7I788z8hjABQg2147h9T8_eG_HWImXQmeJyAWnA',
}

CITIES = {
    'boston':     'aap',
    'newyork':    'aap',
    'sfbay':      'apa',
    #'losangeles': 'apa',
    #'chicago':    'apa',
}

CITY_LOC = {
    #'losangeles': 'CA',
    #'chicago':    'IL',
    'sfbay':      'CA',
    'newyork':    'NY',
    'boston':     'MA',
}

CITY_CENTERS = {
    'boston': (42.355119, -71.083088, 13),
    'newyork': (40.759481, -73.989487, 12),
    #'losangeles': (34.028193, -118.289795, 11),
    #'chicago':    (41.851151, -87.740936, 11),
    'sfbay':      (37.722935, -122.358170, 11),
    }

FROM_EMAIL = "HomeSearchr <no-reply@homesearchr.com>"
EMAIL_SUBJECT = "Your HomeSearchr Results"

# Facebook stuff
FACEBOOK_API_KEY = '372efffa03be3745a604303eb2f6c4f9'
FACEBOOK_SECRET_KEY = '4774852bd302d59b14fa0115b157b928'
FACEBOOK_CALLBACK_PATH = '/facebook/'

YAHOO_APPID = 'u5Q_QtXV34GukrAFoyQi2siRVj7tU7MSLyAlKjmZMJS3u.1VFUV0NEwevKHD3uLjDSHk'

