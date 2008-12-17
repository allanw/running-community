# -*- coding: utf-8 -*-
from settings_pre import *

#ENABLE_PROFILER = True
#ONLY_FORCED_PROFILE = True
#PROFILE_PERCENTAGE = 25
#SORT_PROFILE_RESULTS_BY = 'cumulative' # default is 'time'
#PROFILE_PATTERN = 'ext.db..+\((?:get|get_by_key_name|fetch|count|put)\)'

# Enable I18N and set default language to 'en'
USE_I18N = True
LANGUAGE_CODE = 'en'

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'django.core.context_processors.i18n',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.locale.LocaleMiddleware',
)

GLOBALTAGS = (
    'ragendja.templatetags.ragendjatags',
    'django.templatetags.i18n',
)

# Restrict JS media generation to only the given LOCALE_SITES
#LOCALE_SITES = (
#    LANGUAGE_CODE,
#)

# Increase this when you update your media on the production site, so users
# don't have to refresh their cache. By setting this your MEDIA_URL
# automatically becomes /media/MEDIA_VERSION/
MEDIA_VERSION = 1

# Make this unique, and don't share it with anybody.
SECRET_KEY = '1234567890'

LOGIN_URL = '/account/login/'
LOGOUT_URL = '/account/logout/'
LOGIN_REDIRECT_URL = '/'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.webdesign',
    'appenginepatcher',
    'myapp',
    'registration',
    'mediautils',
)

from settings_post import *
