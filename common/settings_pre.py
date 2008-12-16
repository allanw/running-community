# -*- coding: utf-8 -*-
from appenginepatcher import on_production_server
import os
DEBUG = not on_production_server

ADMINS = ()

DATABASE_ENGINE = 'appengine'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

EMAIL_HOST = 'localhost'
EMAIL_PORT = 25
EMAIL_HOST_USER = 'user'
EMAIL_HOST_PASSWORD = 'password'
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'user@localhost'
SERVER_EMAIL = 'user@localhost'

GLOBALTAGS = (
    'ragendja.templatetags.ragendjatags',
)

LOGIN_REQUIRED_PREFIXES = ()
NO_LOGIN_REQUIRED_PREFIXES = ()

ROOT_URLCONF = 'urls'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'ragendja.template.app_prefixed_loader',
    'django.template.loaders.app_directories.load_template_source',
)

PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))
COMMON_DIR = os.path.dirname(__file__)
MAIN_DIRS = (PROJECT_DIR, COMMON_DIR)

TEMPLATE_DIRS = tuple([os.path.join(dir, 'templates') for dir in MAIN_DIRS])

LOCALE_PATHS = (
    os.path.join(PROJECT_DIR, 'media', 'locale'),
) + tuple([os.path.join(dir, 'locale') for dir in TEMPLATE_DIRS])

FILE_UPLOAD_HANDLERS = (
    'django.core.files.uploadhandler.MemoryFileUploadHandler',
)

CACHE_BACKEND = 'memcached://?timeout=0'

COMBINE_MEDIA = {}
