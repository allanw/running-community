# -*- coding: utf-8 -*-
from settings import *

MEDIA_URL = '/media/%d/' % MEDIA_VERSION

TEMPLATE_DEBUG = DEBUG
MANAGERS = ADMINS

# You can override Django's or some apps' locales with these folders:
if os.path.exists(os.path.join(COMMON_DIR, 'locale_overrides_common')):
    INSTALLED_APPS += ('locale_overrides_common',)
if os.path.exists(os.path.join(PROJECT_DIR, 'locale_overrides')):
    INSTALLED_APPS += ('locale_overrides',)

# Add start markers, so apps can insert JS/CSS at correct position
for combine in ('combined-%(LANGUAGE_CODE)s.js', 'combined.css'):
    COMBINE_MEDIA.setdefault(combine, ())
    COMBINE_MEDIA[combine] = ('!START!',) + COMBINE_MEDIA[combine]
def add_app_media(env, media, *appmedia):
    index = list(env['COMBINE_MEDIA'][media]).index('!START!')
    env['COMBINE_MEDIA'][media] = env['COMBINE_MEDIA'][media][:index] + \
        appmedia + env['COMBINE_MEDIA'][media][index:]

# Import app-specific settings
for app in INSTALLED_APPS:
    try:
        data = __import__(app + '.settings', {}, {}, [''])
        for key, value in data.__dict__.items():
            if not key.startswith('_'):
                globals()[key] = value
    except ImportError:
        pass

# Remove start markers
for combine in ('combined-%(LANGUAGE_CODE)s.js', 'combined.css'):
    index = list(COMBINE_MEDIA[combine]).index('!START!')
    COMBINE_MEDIA[combine] = COMBINE_MEDIA[combine][:index] + \
        COMBINE_MEDIA[combine][index+1:]

try:
    from settings_overrides import *
except ImportError:
    pass
