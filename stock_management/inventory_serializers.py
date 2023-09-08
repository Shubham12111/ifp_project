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
        max_length=255,
        min_length=5,
        required=True,
        style={
            'base_template': 'custom_fullwidth_input.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Address is required.",
        },
        
    )
    
    country = serializers.PrimaryKeyRelatedField(
        queryset=Country.objects.all(),
        default=None,
        style={
            'base_template': 'custom_select.html'
        },
    )
    town = serializers.PrimaryKeyRelatedField(
        queryset=City.objects.all(),
        default=None,
        style={
            'base_template': 'custom_select.html'
        },
    )
    county = serializers.PrimaryKeyRelatedField(
        queryset=Region.objects.all(),
        default=None,
        style={
            'base_template': 'custom_select.html'
        },
    )
    post_code = serializers.CharField(
        max_length=7,
        required=True,
        allow_blank=True,
        allow_null=True,
        style={
            'base_template': 'custom_input.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Post Code is required.",
        },
        validators=[validate_uk_postcode] 
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
