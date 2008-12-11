from django.core.serializers.__original__.base import *
from django.core.serializers.__original__ import base
class DeserializedObject(base.DeserializedObject):
    def save(self, save_m2m=True):
        self.object.save()
        self.object._parent = None
base.DeserializedObject = DeserializedObject
