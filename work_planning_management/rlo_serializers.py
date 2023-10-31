from rest_framework import serializers
from authentication.models import User
import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags
from django.core.validators import FileExtensionValidator

from rest_framework import serializers
from rest_framework.fields import empty

from authentication.models import User
from infinity_fire_solutions.custom_form_validation import *
from infinity_fire_solutions.aws_helper import *

from .models import *


class JobField(serializers.PrimaryKeyRelatedField):
    """
    Primary key related field for Job model.

    This field is used for relating Job model instances to other models.

    Methods:
        get_queryset: Get the queryset for Job instances.
    """
    def get_queryset(self):
        """
        Get the queryset for Job instances.

        Returns:
            QuerySet: A queryset of Job instances filtered by status.
        """
       
        return Job.objects.exclude(quotation__status='approved')

class RLOAddSerializer(serializers.ModelSerializer):
    """
    Serializer for adding a new RLO.

    Fields:
    - name - name of RLO
    - job - job associated with RLO.
    """
    name = serializers.CharField(
        label=('RLO Name'),
        required=True, 
        style={
            'base_template': 'custom_input.html'
            },
        error_messages={
            "required": "This field is required.",
            "blank": "RLO Name is required.",
            "null": "RLO Name is required."
        },   
    )
    
    job = JobField(
        label=('RLO Job'),
        required=True,
        allow_null=True,  # Set allow_null to True
        style={'base_template': 'custom_select.html',
               "autofocus": False,
               "autocomplete": "off",
               
               },
        error_messages={
            "required": "This field is required.",
            "blank": "RLO Job is required.",
        },
    )
    
    class Meta:
        model = RLO
        fields = ('name','job')



class RLOLetterTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RLOLetterTemplate
        fields = '__all__'




