# -*- coding: utf-8 -*-
from django.test import TestCase
from ragendja.testutils import ModelTestCase
from google.appengine.ext import db
from google.appengine.ext.db.polymodel import PolyModel

# Test class Meta

class TestA(db.Model):
    class Meta:
        abstract = True
        verbose_name = 'aaa'

class TestB(TestA):
    class Meta:
        verbose_name = 'bbb'

class TestC(TestA):
    pass

class PolyA(PolyModel):
    class Meta:
        verbose_name = 'polyb'

class PolyB(PolyA):
    pass

class ModelMetaTest(TestCase):
    def test_class_meta(self):
        self.assertEqual(TestA._meta.verbose_name_plural, 'aaas')
        self.assertTrue(TestA._meta.abstract)

        self.assertEqual(TestB._meta.verbose_name_plural, 'bbbs')
        self.assertFalse(TestB._meta.abstract)

        self.assertEqual(TestC._meta.verbose_name_plural, 'test cs')
        self.assertFalse(TestC._meta.abstract)

        self.assertFalse(PolyA._meta.abstract)
        self.assertFalse(PolyB._meta.abstract)

# Test signals

class SignalTest(TestCase):
    def test_signals(self):
        from django.db.models.signals import pre_delete
        global received
        received = False
        def handle_pre_delete(signal, sender, instance):
            global received
            received = True
        pre_delete.connect(handle_pre_delete, sender=TestC)
        a = TestC()
        a.put()
        a.delete()
        self.assertTrue(received)

# Test serialization

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

