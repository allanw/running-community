# -*- coding: utf-8 -*-
from django.db.models import permalink
from google.appengine.ext import db

class Person(db.Model):
    """Basic user profile with personal details."""
    first_name = db.StringProperty(required=True)
    last_name = db.StringProperty(required=True)

    def __unicode__(self):
        return '%s %s' % (self.first_name, self.last_name)

    @permalink
    def get_absolute_url(self):
        return ('myapp.views.show_person', (), {'key': self.key()})

class Pet(db.Model):
    owner = db.ReferenceProperty(Person,required=True, collection_name='pet_set')
    name = db.StringProperty(required=True)

class Contract(db.Model):
    employer = db.ReferenceProperty(Person,required=True, collection_name='employee_contract_set')
    employee = db.ReferenceProperty(Person,required=True, collection_name='employer_contract_set')
    start_date = db.DateTimeProperty()
    end_date = db.DateTimeProperty()
