# -*- coding: utf-8 -*-
# Unfortunately, we have to fix a few App Engine bugs here because otherwise
# not all of our features will work. Still, we should keep the number of bug
# fixes to a minimum and report everything to Google, please:
# http://code.google.com/p/googleappengine/issues/list

from google.appengine.ext import db
import logging, new, os, sys

base_path = os.path.abspath(os.path.dirname(__file__))

def patch_package(original_name, path):
    original = __import__(original_name, {}, {}, [''])
    patched = new.module(original_name)
    patched.__path__ = original.__path__[:]
    original.__path__.insert(0, os.path.join(base_path, path))
    sys.modules[original_name + '.__original__'] = patched

def patch_all():
    patch_python()
    patch_app_engine()
    patch_django()
    setup_logging()

def patch_python():
    # Remove modules that we want to override
    for module in ('httplib', 'urllib', 'urllib2', 'memcache',):
        if module in sys.modules:
            del sys.modules[module]

    # For some reason the imp module can't be replaced via sys.path
    from appenginepatcher import have_appserver
    if have_appserver:
        from appenginepatcher import imp
        sys.modules['imp'] = imp

    # Add fake error and gaierror to socket module. Required for boto support.
    import socket
    class error(Exception):
        pass
    class gaierror(Exception):
        pass
    socket.error = error
    socket.gaierror = gaierror

    if have_appserver:
        def unlink(_):
            raise NotImplementedError('App Engine does not support FS writes!')
        os.unlink = unlink

def patch_app_engine():
    # This allows for using Paginator on a Query object. We limit the number
    # of results to 301, so there won't be any timeouts (301, so you can say
    # "more than 300 results").
    def __len__(self):
        return self.count(301)
    db.Query.__len__ = __len__

    # Add "model" property to Query (needed by generic views)
    class ModelProperty(object):
        def __get__(self, query, unused):
            try:
                return query._Query__model_class
            except:
                return query._model_class
    db.Query.model = ModelProperty()

    # Add a few Model methods that are needed for serialization
    def _get_pk_val(self):
        return unicode(self.key())
    db.Model._get_pk_val = _get_pk_val
    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self._get_pk_val() == other._get_pk_val()
    db.Model.__eq__ = __eq__
    def __ne__(self, other):
        return not self.__eq__(other)
    db.Model.__ne__ = __ne__

    # Make Property more Django-like (needed for serialization)
    db.Property.serialize = True
    db.Property.rel = None
    def attname(self):
        return self.name
    db.Property.attname = property(attname)
    class Relation(object):
        field_name = 'key_name'
    db.ReferenceProperty.rel = Relation

    # Add repr to make debugging a little bit easier
    def __repr__(self):
        d = dict([(k, getattr(self, k)) for k in self.properties()])
        return '%s(**%s)' % (self.__class__.__name__, repr(d))
    db.Model.__repr__ = __repr__

    # Replace save() method with one that calls put(), so a monkey-patched
    # put() will also work if someone uses save()
    def save(self):
        return self.put()
    db.Model.save = save

    # Add _meta to Model, so porting code becomes easier (generic views,
    # xheaders, and serialization depend on it).
    class _meta(object):
        many_to_many = []
        class pk:
            name = 'key_name'

        def __init__(self, model):
            try:
                self.app_label = model.__module__.split('.')[-2]
            except IndexError:
                raise ValueError('Django expects models (here: %s.%s) to be defined in their own apps!' % (model.__module__, model.__name__))
            self.object_name = model.__name__
            self.module_name = self.object_name.lower()
            self.verbose_name = self.object_name.lower()
            self.verbose_name_plural = None
            self.abstract = False
            self.model = model

        def __str__(self):
            return '%s.%s' % (self.app_label, self.module_name)

        @property
        def local_fields(self):
            return self.model.properties().values()

    # Register models with Django
    old_init = db.PropertiedClass.__init__
    def __init__(cls, name, bases, attrs):
        """Creates a combined appengine and Django model.

        The resulting model will be known to both the appengine libraries and
        Django.
        """
        cls._meta = _meta(cls)
        cls._default_manager = cls
        old_init(cls, name, bases, attrs)
        from django.db.models.loading import register_models
        register_models(cls._meta.app_label, cls)
    db.PropertiedClass.__init__ = __init__

def fix_app_engine_bugs():
    #### Now we fix bugs in App Engine

    # Fix handling of verbose_name. Google resolves lazy translation objects
    # immedately which of course breaks translation support.
    # http://code.google.com/p/googleappengine/issues/detail?id=583
    from django import forms
    from django.utils.text import capfirst
    # This import is needed, so the djangoforms patch can do its work, first
    from google.appengine.ext.db import djangoforms
    def get_form_field(self, form_class=forms.CharField, **kwargs):
        defaults = {'required': self.required}
        if self.verbose_name:
            defaults['label'] = capfirst(self.verbose_name)
        if self.choices:
            choices = []
            if not self.required or (self.default is None and
                                     'initial' not in kwargs):
                choices.append(('', '---------'))
            for choice in self.choices:
                choices.append((str(choice), unicode(choice)))
            defaults['widget'] = forms.Select(choices=choices)
        if self.default is not None:
            defaults['initial'] = self.default
        defaults.update(kwargs)
        return form_class(**defaults)
    db.Property.get_form_field = get_form_field

    # Extend ModelForm with support for EmailProperty
    # http://code.google.com/p/googleappengine/issues/detail?id=880
    def get_form_field(self, **kwargs):
        """Return a Django form field appropriate for an email property."""
        defaults = {'form_class': forms.EmailField}
        defaults.update(kwargs)
        return super(db.EmailProperty, self).get_form_field(**defaults)
    db.EmailProperty.get_form_field = get_form_field

    # Fix default value of UserProperty (Google resolves the user too early)
    # http://code.google.com/p/googleappengine/issues/detail?id=879
    from django.utils.functional import lazy
    from google.appengine.api import users
    def get_form_field(self, **kwargs):
        defaults = {'initial': lazy(users.GetCurrentUser, users.User)}
        defaults.update(kwargs)
        return super(db.UserProperty, self).get_form_field(**defaults)
    db.UserProperty.get_form_field = get_form_field

def log_exception(*args, **kwargs):
    logging.exception('Exception in request:')

def patch_django():
    # In order speed things up and consume less memory we lazily replace
    # modules if possible. This requires some __path__ magic. :)

    # Add fake 'appengine' DB backend
    # This also creates a separate datastore for each project.
    from appenginepatcher.db_backends import appengine
    sys.modules['django.db.backends.appengine'] = appengine

    # Replace generic views
    patch_package('django.views.generic', 'generic_views')

    # Replace db session backend and tests
    patch_package('django.contrib.sessions', 'sessions')
    patch_package('django.contrib.sessions.backends', 'session_backends')

    # Replace auth models and other apps in contrib that have a non-empty
    # __init__.py
    patch_package('django.contrib', 'contrib')

    # Patch serializers
    patch_package('django.core.serializers', 'serializers')

    # Replace ModelForm
    from google.appengine.ext.db import djangoforms
    from django import forms
    from django.forms import models as modelforms
    forms.ModelForm = modelforms.ModelForm = djangoforms.ModelForm
    forms.ModelFormMetaclass = djangoforms.ModelFormMetaclass
    modelforms.ModelFormMetaclass = djangoforms.ModelFormMetaclass

    # Replace mail backend.
    # This can't be done with patch_package() because the test environment
    # monkey-patches SMTPConnection and this has to be done on the original
    # module instead of a "proxy".
    from appenginepatcher import mail as gmail
    from django.core import mail
    mail.SMTPConnection = gmail.GoogleSMTPConnection
    mail.mail_admins = gmail.mail_admins
    mail.mail_managers = gmail.mail_managers

    fix_app_engine_bugs()

    # Fix translation support if we're in a zip file. We change the path
    # of the django.conf module, so the translation code tries to load
    # Django's translations from the common/django-locale/locale folder.
    from django import conf
    from aecmd import COMMON_DIR
    if '.zip' + os.sep in conf.__file__:
        conf.__file__ = os.path.join(COMMON_DIR, 'django-locale', 'fake.py')

    # Patch login_required if using Google Accounts
    from django.conf import settings
    if 'ragendja.auth.middleware.GoogleAuthenticationMiddleware' in \
            settings.MIDDLEWARE_CLASSES:
        from ragendja.auth.decorators import google_login_required, \
            redirect_to_google_login
        from django.contrib.auth import decorators, views
        decorators.login_required = google_login_required
        views.redirect_to_login = redirect_to_google_login

    # Log errors.
    from django.core import signals
    signals.got_request_exception.connect(log_exception)

    # Unregister the rollback event handler.
    import django.db
    signals.got_request_exception.disconnect(django.db._rollback_on_exception)

    # Activate ragendja's GLOBALTAGS support (automatically done on import)
    from ragendja import template

def setup_logging():
    from django.conf import settings
    if settings.DEBUG:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)
