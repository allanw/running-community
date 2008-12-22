# -*- coding: utf-8 -*-
from django.db.models import permalink
from google.appengine.ext import db
from ragendja.dbutils import delete_relations

class Person(db.Model):
    """Basic user profile with personal details."""
    first_name = db.StringProperty(required=True)
    last_name = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)

    def __unicode__(self):
        return '%s %s' % (self.first_name, self.last_name)

    @permalink
    def get_absolute_url(self):
        return ('myapp.views.show_person', (), {'key': self.key()})

    def delete(self):
        # Also delete related entities
        delete_relations(self, 'file_set', 'employee_contract_set',
            'employer_contract_set')
        super(Person, self).delete()

class File(db.Model):
    owner = db.ReferenceProperty(Person,required=True, collection_name='file_set')
    name = db.StringProperty(required=True)
    file = db.BlobProperty(required=True)

    @permalink
    def get_absolute_url(self):
        return ('myapp.views.download_file', (), {'key': self.key(),
                                                  'name': self.name})

class Contract(db.Model):
    employer = db.ReferenceProperty(Person,required=True, collection_name='employee_contract_set')
    employee = db.ReferenceProperty(Person,required=True, collection_name='employer_contract_set')
    start_date = db.DateTimeProperty()
    end_date = db.DateTimeProperty()
