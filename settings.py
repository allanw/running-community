# -*- coding: utf-8 -*-
from settings_pre import *

#ENABLE_PROFILER = True
#ONLY_FORCED_PROFILE = True
#PROFILE_PERCENTAGE = 25
#SORT_PROFILE_RESULTS_BY = 'cumulative' # default is 'time'
#PROFILE_PATTERN = 'ext.db..+\((?:get|get_by_key_name|fetch|count|put)\)'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '1234567890'

LOGIN_REDIRECT_URL = '/'

# Extend the list of installed apps defined in common/settings_pre.py
INSTALLED_APPS += (
    'myapp',
    'registration',
)

ACCOUNT_ACTIVATION_DAYS = 3

from settings_post import *
