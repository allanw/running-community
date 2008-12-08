# -*- coding: utf-8 -*-
from settings import *

# Import app-specific settings
for app in INSTALLED_APPS:
    try:
        data = __import__(app + '.settings', {}, {}, [''])
        for key, value in data.__dict__.items():
            if not key.startswith('_'):
                globals()[key] = value
    except ImportError:
        pass

try:
    from settings_overrides import *
except ImportError:
    pass

TEMPLATE_DEBUG = DEBUG
MANAGERS = ADMINS

# You can override Django's or some apps' locales with these folders:
if os.path.exists(os.path.join(COMMON_DIR, 'locale_overrides_common')):
    INSTALLED_APPS += ('locale_overrides_common',)
if os.path.exists(os.path.join(PROJECT_DIR, 'locale_overrides')):
    INSTALLED_APPS += ('locale_overrides',)
