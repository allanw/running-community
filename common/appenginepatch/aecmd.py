# -*- coding: utf-8 -*-
import os, sys

COMMON_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
PROJECT_DIR = os.path.dirname(COMMON_DIR)
ZIP_PACKAGES_DIRS = (os.path.join(PROJECT_DIR, 'zip-packages'),
                     os.path.join(COMMON_DIR, 'zip-packages'))
# Overrides for os.environ
env_ext = {'DJANGO_SETTINGS_MODULE': 'settings'}

def setup_env(manage_py_env=False):
    """Configures app engine environment for command-line apps."""
    # Try to import the appengine code from the system path.
    try:
        from google.appengine.api import apiproxy_stub_map
    except ImportError, e:
        # Not on the system path. Build a list of alternative paths where it
        # may be. First look within the project for a local copy, then look for
        # where the Mac OS SDK installs it.
        paths = [os.path.join(COMMON_DIR, '.google_appengine'),
                 '/usr/local/google_appengine']
        for path in os.environ.get('PATH', '').replace(';', ':').split(':'):
            path = path.rstrip(os.sep)
            if path.endswith('google_appengine'):
                paths.append(path)
        if os.name in ('nt', 'dos'):
            prefix = '%(PROGRAMFILES)s' % os.environ
            paths.append(prefix + r'\Google\google_appengine')
        # Loop through all possible paths and look for the SDK dir.
        SDK_PATH = None
        for sdk_path in paths:
            if os.path.exists(sdk_path):
                SDK_PATH = sdk_path
                break
        if SDK_PATH is None:
            # The SDK could not be found in any known location.
            sys.stderr.write("The Google App Engine SDK could not be found!\n")
            sys.stderr.write("See README for installation instructions.\n")
            sys.exit(1)
        # Add the SDK and the libraries within it to the system path.
        EXTRA_PATHS = [
            SDK_PATH,
            os.path.join(SDK_PATH, 'lib', 'webob'),
            os.path.join(SDK_PATH, 'lib', 'yaml', 'lib'),
            os.path.join(SDK_PATH, 'lib', 'django'),
        ]
        sys.path = EXTRA_PATHS + sys.path
        from google.appengine.api import apiproxy_stub_map

    # Add this folder to sys.path
    sys.path = [os.path.abspath(os.path.dirname(__file__))] + sys.path

    setup_project()

    from appenginepatcher.patch import patch_all
    patch_all()

    if not manage_py_env:
        return

    print 'Running on app-engine-patch 0.9.3'

def setup_project():
    # Remove the standard version of Django
    for k in [k for k in sys.modules if k.startswith('django')]:
        del sys.modules[k]

    from appenginepatcher import on_production_server
    if on_production_server:
        # This fixes a pwd import bug for os.path.expanduser()
        global env_ext
        env_ext['HOME'] = PROJECT_DIR

    os.environ.update(env_ext)

    # Add the two parent folders and appenginepatcher's lib folder to sys.path.
    # The current folder has to be added in main.py or setup_env(). This
    # suggests a folder structure where you separate reusable code from project
    # code:
    # project -> common -> appenginepatch
    # You can put a custom Django version into the "common" folder, for example.
    EXTRA_PATHS = [
        PROJECT_DIR,
        COMMON_DIR,
    ]

    # We have to import this here, so the stubs use the original Python libs
    # and we can override them for the rest of the code below.
    try:
        from google.appengine.tools import appcfg
        from google.appengine.api import urlfetch_stub
    except ImportError:
        pass

    # Don't yet patch httplib if we'll execute a dev_appserver because
    # urlfetch would get reloaded and then use the wrong httplib.
    this_folder = os.path.abspath(os.path.dirname(__file__))
    EXTRA_PATHS.append(os.path.join(this_folder, 'appenginepatcher', 'lib'))

    # We support zipped packages in the common and project folders.
    # The files must be in the packages folder.
    for packages_dir in ZIP_PACKAGES_DIRS:
        if os.path.isdir(packages_dir):
            for zip_package in os.listdir(packages_dir):
                EXTRA_PATHS.append(os.path.join(packages_dir, zip_package))

    sys.path = EXTRA_PATHS + sys.path
