import re
import uuid
from .models import *
from django.db import transaction
from rest_framework import serializers
from infinity_fire_solutions.aws_helper import *
from infinity_fire_solutions.custom_form_validation import *
from django.conf import settings

class InventoryLocationSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        max_length=255,
        min_length=3,
        required=True,
        style={
            'base_template': 'custom_fullwidth_input.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Name is required.",
            "min_length": "Name must consist of at least 3 characters."
        },
        validators = [validate_name]
        
    )
    address = serializers.CharField(
        label='Address',
        max_length=255,
        required=False,
        style={
           "input_type": "text",
            "autocomplete": "off",
            "autofocus": False,
            
        },
    )
    
    country = serializers.CharField(
        label=('Country'),
        default=None,
        style={
            'base_template': 'custom_input.html'
        },
    )

    town = serializers.CharField(
        label=('Town'),
        default=None,
        style={
            'base_template': 'custom_input.html'
        },
    )
    county = serializers.CharField(
        label=('County'),
        style={
            'base_template': 'custom_input.html'
        },
    )
    post_code = serializers.ChoiceField(
        label=('Post Code'),
        required=True,
        choices=POST_CODE_LIST,
        style={
            'base_template': 'custom_select.html'
        },


    )
    description = serializers.CharField(
        max_length=1024, 
        required=True, 
        style={'base_template': 'rich_textarea.html'},
        error_messages={
            "required": "This field is required.",
            "blank": "Description is required.",
        },
        validators=[validate_description],
    )
    class Meta:
        model = InventoryLocation
        fields = ['name' ,'description','address','country', 'town', 'county', 'post_code']
class PostCodeInfoSerializer(serializers.Serializer):
    post_code = serializers.CharField(max_length=255)
    town = serializers.CharField(max_length=255)
    county = serializers.CharField(max_length=255)
    country = serializers.CharField(max_length=255)