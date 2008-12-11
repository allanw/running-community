from django.core.serializers.__original__.pyyaml import *
from django.core.serializers.__original__ import pyyaml
from python import Deserializer as PythonDeserializer
pyyaml.PythonDeserializer = PythonDeserializer
