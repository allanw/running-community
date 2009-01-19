# -*- coding: utf-8 -*-
# Unfortunately, we have to fix a few App Engine bugs here because otherwise
# not all of our features will work. Still, we should keep the number of bug
# fixes to a minimum and report everything to Google, please:
# http://code.google.com/p/googleappengine/issues/list

from google.appengine.ext import db
import logging, new, os, re, sys

base_path = os.path.abspath(os.path.dirname(__file__))

get_verbose_name = lambda class_name: re.sub('(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))', ' \\1', class_name).lower().strip()

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

    from appenginepatcher import socketpatch

    if have_appserver:
        def unlink(_):
            raise NotImplementedError('App Engine does not support FS writes!')
        os.unlink = unlink

        # urllib2.randombytes checks for /dev/urandom and then opens the file
        # without any further checks (failing)
        old_exists = os.path.exists
        def exists(path):
            if path == '/dev/urandom':
                return False
            return old_exists(path)
        os.path.exists = exists

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

    # Add a few Model methods that are needed for serialization and ModelForm
    def _get_pk_val(self):
        if self.has_key():
            return unicode(self.key())
        else:
            return None
    db.Model._get_pk_val = _get_pk_val
    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self._get_pk_val() == other._get_pk_val()
    db.Model.__eq__ = __eq__
    def __ne__(self, other):
        return not self.__eq__(other)
    db.Model.__ne__ = __ne__
    def pk(self):
        return self._get_pk_val()
    db.Model.id = db.Model.pk = property(pk)

    # Make Property more Django-like (needed for serialization and ModelForm)
    db.Property.serialize = True
    db.Property.editable = True

    def attname(self):
        return self.name
    db.Property.attname = property(attname)

    class Rel(object):
        field_name = 'key'

        def __init__(self, property):
            self.property = property
            self.to = property.reference_class

    class RelProperty(object):
        def __get__(self, property, cls):
            if property is None:
                return self
            if not hasattr(property, 'reference_class'):
                return None
            if not hasattr(property, '_rel_cache'):
                property._rel_cache = Rel(property)
            return property._rel_cache
    db.Property.rel = RelProperty()

    def formfield(self, **kwargs):
        return self.get_form_field(**kwargs)
    db.Property.formfield = formfield

    # Add repr to make debugging a little bit easier
    from django.utils.datastructures import SortedDict
    def __repr__(self):
        d = SortedDict()
        if self.has_key() and self.key().name():
            d['key_name'] = self.key().name()
        for field in self._meta.fields:
            try:
                d[field.name] = getattr(self, field.name)
            except:
                d[field.name] = field.get_value_for_datastore(self)
        return u'%s(**%s)' % (self.__class__.__name__, repr(d))
    db.Model.__repr__ = __repr__

    # Add default __str__ and __unicode__ methods
    def __str__(self):
        return unicode(self).encode('utf-8')
    db.Model.__str__ = __str__
    def __unicode__(self):
        return unicode(repr(self))
    db.Model.__unicode__ = __unicode__

    # Replace save() method with one that calls put(), so a monkey-patched
    # put() will also work if someone uses save()
    def save(self):
        self.put()
    db.Model.save = save

    # Add _meta to Model, so porting code becomes easier (generic views,
    # xheaders, and serialization depend on it).
    from django.conf import settings
    from django.utils.encoding import force_unicode, smart_str
    from django.utils.translation import string_concat, get_language, \
        activate, deactivate_all
    class _meta(object):
        many_to_many = ()
        class pk:
            name = 'key'
            attname = 'pk'

        def __init__(self, model):
            try:
                self.app_label = model.__module__.split('.')[-2]
            except IndexError:
                raise ValueError('Django expects models (here: %s.%s) to be defined in their own apps!' % (model.__module__, model.__name__))
            Meta = getattr(model, 'Meta', None)
            self.object_name = model.__name__
            self.module_name = self.object_name.lower()
            self.verbose_name = getattr(Meta,
                'verbose_name', get_verbose_name(self.object_name))
            self.verbose_name_plural = getattr(Meta,
                'verbose_name_plural', string_concat(self.verbose_name, 's'))
            self.ordering = getattr(Meta, 'ordering', ())
            self.abstract = False
            self.model = model
            self.unique_together = ()
            self.installed = model.__module__.rsplit('.', 1)[0] in settings.INSTALLED_APPS
            self.permissions = getattr(Meta, 'permissions', ())
            # XXX: Don't display auth permissions for all extra user models
            if self.app_label != 'auth' or \
                    not (self.object_name.endswith('Traits') or
                         self.object_name == 'EmailUser'):
                self.permissions += (
                    ('add_%s' % self.object_name.lower(),
                        string_concat('Can add ', self.verbose_name)),
                    ('change_%s' % self.object_name.lower(),
                        string_concat('Can change ', self.verbose_name)),
                    ('delete_%s' % self.object_name.lower(),
                        string_concat('Can delete ', self.verbose_name)),
                )

        def __repr__(self):
            return '<Options for %s>' % self.object_name

        def __str__(self):
            return "%s.%s" % (smart_str(self.app_label), smart_str(self.module_name))

        @property
        def verbose_name_raw(self):
            """
            There are a few places where the untranslated verbose name is needed
            (so that we get the same value regardless of currently active
            locale).
            """
            lang = get_language()
            deactivate_all()
            raw = force_unicode(self.verbose_name)
            activate(lang)
            return raw

        @property
        def local_fields(self):
            return tuple(sorted(self.model.properties().values(),
                                key=lambda prop: prop.creation_counter))

        @property
        def fields(self):
            return self.local_fields

        def get_field(self, name, many_to_many=True):
            """
            Returns the requested field by name. Raises FieldDoesNotExist on error.
            """
            from django.db.models.fields import FieldDoesNotExist
            for f in self.fields:
                if f.name == name:
                    return f
            raise FieldDoesNotExist, '%s has no field named %r' % (self.object_name, name)

        def get_add_permission(self):
            return 'add_%s' % self.object_name.lower()

        def get_change_permission(self):
            return 'change_%s' % self.object_name.lower()

        def get_delete_permission(self):
            return 'delete_%s' % self.object_name.lower()

        def get_ordered_objects(self):
            return []

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

    @classmethod
    def kind(cls):
        if getattr(settings, 'DJANGO_STYLE_MODEL_KIND', True):
            return '%s_%s' % (cls._meta.app_label, cls._meta.object_name)
        return cls._meta.object_name
    db.Model.kind = kind

    # This has to come last because we load Django here
    from django.db.models.fields import BLANK_CHOICE_DASH
    def get_choices(self, include_blank=True, blank_choice=BLANK_CHOICE_DASH):
        first_choice = include_blank and blank_choice or []
        if self.choices:
            return first_choice + list(self.choices)
        if self.rel:
            return first_choice + [(obj.pk, unicode(obj))
                                   for obj in self.rel.to.all().fetch(301)]
        return first_choice
    db.Property.get_choices = get_choices

def fix_app_engine_bugs():
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
        else:
            defaults['label'] = self.name.capitalize().replace('_', ' ')
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

    # Fix DateTimeProperty, so it returns a property even for auto_now and
    # auto_now_add.
    # http://code.google.com/p/googleappengine/issues/detail?id=994
    def get_form_field(self, **kwargs):
        defaults = {'form_class': forms.DateTimeField}
        defaults.update(kwargs)
        return super(db.DateTimeProperty, self).get_form_field(**defaults)
    db.DateTimeProperty.get_form_field = get_form_field
    def get_form_field(self, **kwargs):
        defaults = {'form_class': forms.DateField}
        defaults.update(kwargs)
        return super(db.DateProperty, self).get_form_field(**defaults)
    db.DateProperty.get_form_field = get_form_field
    def get_form_field(self, **kwargs):
        defaults = {'form_class': forms.TimeField}
        defaults.update(kwargs)
        return super(db.TimeProperty, self).get_form_field(**defaults)
    db.TimeProperty.get_form_field = get_form_field

    # Fix default value of UserProperty (Google resolves the user too early)
    # http://code.google.com/p/googleappengine/issues/detail?id=879
    from django.utils.functional import lazy
    from google.appengine.api import users
    def get_form_field(self, **kwargs):
        defaults = {'initial': lazy(users.GetCurrentUser, users.User)()}
        defaults.update(kwargs)
        return super(db.UserProperty, self).get_form_field(**defaults)
    db.UserProperty.get_form_field = get_form_field

    # Fix file uploads via BlobProperty
    def get_form_field(self, **kwargs):
        defaults = {'form_class': forms.FileField}
        defaults.update(kwargs)
        return super(db.BlobProperty, self).get_form_field(**defaults)
    db.BlobProperty.get_form_field = get_form_field
    def get_value_for_form(self, instance):
        return getattr(instance, self.name)
    db.BlobProperty.get_value_for_form = get_value_for_form
    from django.core.files.uploadedfile import UploadedFile
    def make_value_from_form(self, value):
        if isinstance(value, UploadedFile):
            return db.Blob(value.read())
        return super(db.BlobProperty, self).make_value_from_form(value)
    db.BlobProperty.make_value_from_form = make_value_from_form

    # Optimize ReferenceProperty, so it returns the key directly
    # http://code.google.com/p/googleappengine/issues/detail?id=993
    def get_value_for_form(self, instance):
        return self.get_value_for_datastore(instance)
    db.ReferenceProperty.get_value_for_form = get_value_for_form
    # Use our ModelChoiceField instead of Google's
    def get_form_field(self, **kwargs):
        defaults = {'form_class': forms.ModelChoiceField,
                    'queryset': self.reference_class.all()}
        defaults.update(kwargs)
        return super(db.ReferenceProperty, self).get_form_field(**defaults)
    db.ReferenceProperty.get_form_field = get_form_field

def log_exception(*args, **kwargs):
    logging.exception('Exception in request:')

def patch_django():
    # Most patches are part of the django-app-engine project:
    # http://www.bitbucket.org/wkornewald/django-app-engine/

    fix_app_engine_bugs()

    # Fix translation support if we're in a zip file. We change the path
    # of the django.conf module, so the translation code tries to load
    # Django's translations from common/django_aep_export/django-locale/locale
    from django import conf
    from aecmd import COMMON_DIR
    if '.zip' + os.sep in conf.__file__:
        conf.__file__ = os.path.join(COMMON_DIR, 'django_aep_export',
                                     'django-locale', 'fake.py')

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
