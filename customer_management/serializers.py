import uuid
from django.core.validators import RegexValidator

from rest_framework import serializers
from cities_light.models import City, Country, Region
from rest_framework.validators import UniqueValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator
from django.conf import settings
from infinity_fire_solutions.aws_helper import *
import re
from .models import *

class CustomerSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = ('__all__')