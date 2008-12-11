# -*- coding: utf-8 -*-
import os, sys

# Add current folder to sys.path, so we can import aecmd
current_dir = os.path.abspath(os.path.dirname(__file__))
sys.path = [current_dir] + sys.path

from aecmd import setup_project
setup_project()

from appenginepatcher.patch import patch_all, setup_logging
patch_all()

# TODO: Remove this and the respective code in real_main() and profile_main()
# when this App Engine bug is fixed:
# http://code.google.com/p/googleappengine/issues/detail?id=772
path_backup = sys.path[:]
env_ext = {'DJANGO_SETTINGS_MODULE': 'settings'}
if 'HOME' in os.environ:
    env_ext['HOME'] = os.environ['HOME']

import django.core.handlers.wsgi
from google.appengine.ext.webapp import util
from django.conf import settings

def real_main():
    sys.path[:] = path_backup
    os.environ.update(env_ext)
    setup_logging()

    # Create a Django application for WSGI.
    application = django.core.handlers.wsgi.WSGIHandler()

    # Run the WSGI CGI handler with that application.
    util.run_wsgi_app(application)

def profile_main():
    import logging, cProfile, pstats, random, StringIO
    only_forced_profile = getattr(settings, 'ONLY_FORCED_PROFILE', False)
    profile_percentage = getattr(settings, 'PROFILE_PERCENTAGE', None)
    if (only_forced_profile and
                'profile=forced' not in os.environ.get('QUERY_STRING')) or \
            (not only_forced_profile and profile_percentage and
                float(profile_percentage) / 100.0 <= random.random()):
        return real_main()

    prof = cProfile.Profile()
    prof = prof.runctx('real_main()', globals(), locals())
    stream = StringIO.StringIO()
    stats = pstats.Stats(prof, stream=stream)
    sort_by = getattr(settings, 'SORT_PROFILE_RESULTS_BY', 'time')
    if not isinstance(sort_by, (list, tuple)):
        sort_by = (sort_by,)
    stats.sort_stats(*sort_by)

    restrictions = []
    profile_pattern = getattr(settings, 'PROFILE_PATTERN', None)
    if profile_pattern:
        restrictions.append(profile_pattern)
    max_results = getattr(settings, 'MAX_PROFILE_RESULTS', 80)
    if max_results and max_results != 'all':
        restrictions.append(max_results)
    stats.print_stats(*restrictions)
    extra_output = getattr(settings, 'EXTRA_PROFILE_OUTPUT', None) or ()
    if not isinstance(sort_by, (list, tuple)):
        extra_output = (extra_output,)
    if 'callees' in extra_output:
        stats.print_callees()
    if 'callers' in extra_output:
        stats.print_callers()
    logging.info('Profile data:\n%s', stream.getvalue())

main = getattr(settings, 'ENABLE_PROFILER', False) and profile_main or real_main

if __name__ == '__main__':
    main()
