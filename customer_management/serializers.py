from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from infinity_fire_solutions.aws_helper import *
from infinity_fire_solutions.custom_form_validation import *
from authentication.models import CUSTOMER_TYPES, User
from rest_framework.validators import UniqueValidator
from .models import *
import re


class ContactCustomerSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(
        label=('First Name '),
        required=True,
        max_length=50,
        style={
            "input_type": "text",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
            'base_template': 'custom_input.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "First Name is required.",
            "invalid": "First Name can only contain characters.",

        },
        validators=[validate_first_name] 
        
    )
    
    last_name = serializers.CharField(
        label=('Last Name '),
        required=True,
        max_length=50,
        style={
            "input_type": "text",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
            'base_template': 'custom_input.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Last Name is required.",
            "invalid": "Last Name can only contain characters.",
        },
        validators=[validate_last_name] 
    )
    
    email = serializers.EmailField(
        label=('Email '),
        validators=[UniqueValidator(queryset=User.objects.all(), message="Email already exists. Please use a different email.")],
        required=True,
        max_length=100,
        style={
            "input_type": "email",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
            'base_template': 'custom_input.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Email is required.",
        },
    )
    
    phone_number = serializers.CharField(
        label='Phone Number',
        max_length=14,
        min_length=10,
        required=False,
        style={
            'base_template': 'custom_input.html'
        },
        validators=[validate_phone_number] 
    )
    company_name = serializers.CharField(
        label=('Company Name'),
        max_length=100,
        min_length=3,
        required=False,
        
    )
  
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email','company_name','phone_number')
  
  
class CustomerSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(
        label=('First Name '),
        required=True,
        max_length=50,
        style={
            "input_type": "text",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
            'base_template': 'custom_input.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "First Name is required.",
            "invalid": "First Name can only contain characters.",

        },
        validators=[validate_first_name] 
        
    )
    
    last_name = serializers.CharField(
        label=('Last Name '),
        required=True,
        max_length=50,
        style={
            "input_type": "text",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
            'base_template': 'custom_input.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Last Name is required.",
            "invalid": "Last Name can only contain characters.",
        },
        validators=[validate_last_name] 
    )
    
    email = serializers.EmailField(
        label=('Email '),
        validators=[UniqueValidator(queryset=User.objects.all(), message="Email already exists. Please use a different email.")],
        required=True,
        max_length=100,
        style={
            "input_type": "email",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
            'base_template': 'custom_input.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Email is required.",
        },
    )
    phone_number = serializers.CharField(
        label='Phone Number',
        max_length=14,
        min_length=10,
        required=False,
        style={
            'base_template': 'custom_input.html'
        },
        validators=[validate_phone_number] 
    )
    company_name = serializers.CharField(
        label=('Company Name'),
        max_length=100,
        min_length=3,
        required=True,
        style={
            "input_type": "text",
            "autocomplete": "off",
            "autofocus": False,
            "base_template": 'custom_input.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Company Name is required.",
            "min_length": "Company name must consist of at least 3 characters."
        },
        validators=[validate_company_name] 
    )
    customer_type = serializers.ChoiceField(
        label='Customer Type',
        choices=CUSTOMER_TYPES,
        default='individual',
        style={
            'base_template': 'custom_select.html',
            'custom_class': 'col-6'
        },
    )
   
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email','company_name','phone_number','customer_type')


    def update(self, instance, validated_data):
        """
        Update and save the instance.
        Args:
            instance: The existing object instance.
            validated_data: The validated data to update the instance.
        Returns:
            instance: The updated instance.
        """
        # Check if 'phone_number' field is present in validated data
        if 'phone_number' in validated_data:
            # If phone number is provided, update it
            instance.phone_number = validated_data.pop('phone_number')
        else:
            # If phone number is not provided, remove it from the instance
            instance.phone_number = None
        # Update and save the instance with other validated data
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
        
        
    
class BillingAddressSerializer(serializers.ModelSerializer):
    vat_number = serializers.CharField(
        label='Vat Number',
        required=True,
        style={
            'base_template': 'custom_input.html'
        },
    )
    pan_number = serializers.CharField(
        label='NION',
        required=True,
        style={
            'base_template': 'custom_input.html'
        },
    )
    place_to_supply = serializers.CharField(
        label='Place To Supply',
        required=False,
        max_length=50,
        style={
            'base_template': 'custom_input.html'
        },
    )
    tax_preference = serializers.ChoiceField(
        label='Tax Preference',
        choices=TAX_PREFERENCE_CHOICES,
        default='taxable',
        style={
            'base_template': 'custom_select.html',
            'custom_class': 'col-6'
        },
    )
   
    address = serializers.CharField(
        max_length=255,
        min_length=5,
        required=False,
        allow_blank=True,
        allow_null=True,
        
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
        required=False,
        allow_blank=True,
        allow_null=True,
        style={
            'base_template': 'custom_input.html'
        },
        validators=[validate_uk_postcode] 
    )
    
    def validate_vat_number(self, value):
        # Custom validation for VAT number format (United Kingdom VAT number)
        if not re.match(r'^\d{9}$', value):
            raise serializers.ValidationError("Invalid VAT number format. It should be a 9-digit number.")
        return value
    
    def validate_pan_number(self, value):
        # Custom validation for NION format (National Insurance Number in the UK)
        if not re.match(r'^[A-Z]{2}\d{6}[A-Z]$', value):
            raise serializers.ValidationError("Invalid NION format. It should consist of two letters, six digits, and a final letter (e.g., AB123456C).")
        return value
    
    class Meta:
        model = BillingAddress
        fields = ['vat_number', 'pan_number', 'place_to_supply', 'tax_preference', 'address',
                  'country', 'town', 'county', 'post_code']
        

class SiteAddressSerializer(serializers.ModelSerializer):
    site_name = serializers.CharField(
        max_length=255,
        min_length=3,
        required=True,
        style={
            'base_template': 'custom_fullwidth_input.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Site Name is required.",
            "min_length": "Site name must consist of at least 3 characters."
        },
        
    )
    address = serializers.CharField(
        max_length=255,
        min_length=5,
        required=True,
        style={
            'base_template': 'custom_fullwidth_input.html'
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
        validators=[validate_uk_postcode] 
    )
    
    class Meta:
        model = SiteAddress
        fields = ['site_name' ,'address','country', 'town', 'county', 'post_code']
        


class ContactPersonSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(
        label=('First Name '),
        required=True,
        max_length=100,
        style={
            "input_type": "text",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
            'base_template': 'custom_input.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "First Name is required.",
            "invalid": "First Name can only contain characters.",

        },
        validators=[validate_first_name] 
    )
    
    last_name = serializers.CharField(
        label=('Last Name '),
        required=True,
        max_length=100,
        style={
            "input_type": "text",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
            'base_template': 'custom_input.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Last Name is required.",
            "invalid": "Last Name can only contain characters.",
        },
        validators=[validate_last_name] 
    )
    
    email = serializers.EmailField(
        label=('Email '),
        required=True,
        max_length=100,
        style={
            "input_type": "email",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
            'base_template': 'custom_input.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Email is required.",
        },
    )
    phone_number = serializers.CharField(
        label='Phone Number',
        max_length=14,
        min_length=10,
        required=False,
        style={
            'base_template': 'custom_input.html'
        },
        validators=[validate_phone_number] 
    )
    class Meta:
        model = ContactPerson
        fields = ['first_name' ,'last_name','email', 'phone_number']