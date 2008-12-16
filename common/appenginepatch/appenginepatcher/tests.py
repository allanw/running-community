# -*- coding: utf-8 -*-
from ragendja.testutils import ModelTestCase
from google.appengine.ext import db

class SerializeModel(db.Model):
    name = db.StringProperty()
    count = db.IntegerProperty()

class SerializerTest(ModelTestCase):
    model = SerializeModel

    def test_serializer(self, format='json'):
        from django.core import serializers
        x = SerializeModel(key_name='blue_key', name='blue', count=4)
        x.put()
        SerializeModel(name='green', count=1).put()
        data = serializers.serialize(format, SerializeModel.all())
        db.delete(SerializeModel.all().fetch(100))
        for obj in serializers.deserialize(format, data):
            obj.save()
        self.validate_state(
            ('key.name', 'name',  'count'),
            (None,       'green', 1),
            ('blue_key', 'blue',  4),
        )

    def test_xml_serializer(self):
        self.test_serializer(format='xml')

    def test_python_serializer(self):
        self.test_serializer(format='python')

    def test_yaml_serializer(self):
        self.test_serializer(format='yaml')
