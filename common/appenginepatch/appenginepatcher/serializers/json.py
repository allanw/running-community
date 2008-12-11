from django.core.serializers.__original__.json import *
from django.core.serializers.__original__ import json
from python import Deserializer as PythonDeserializer
json.PythonDeserializer = PythonDeserializer
