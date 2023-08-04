from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from infinity_fire_solutions.aws_helper import *
from authentication.models import CUSTOMER_TYPES, User
from rest_framework.validators import UniqueValidator
from .models import *
import re

def validate_phone_number(value):
    # Remove any non-digit characters from the input
    cleaned_number = re.sub(r'\D', '', value)

    # Check if the cleaned number has exactly 12 digits
    if len(cleaned_number) != 12:
        raise serializers.ValidationError("Phone number should have 12 digits, including the country code.")

    # Check if the cleaned number starts with the country code +44
    if not cleaned_number.startswith('44'):
        raise serializers.ValidationError("Phone number should start with the country code +44.")

    return value

def validate_uk_postcode(value):
    # Remove any spaces from the input
    cleaned_postcode = value.replace(' ', '').upper()

    # Define a regular expression pattern for a valid UK postcode
    pattern = r'^[A-Z]{1,2}\d{1,2}[A-Z]?\d[A-Z]{2}$'

    # Check if the cleaned postcode matches the pattern
    if not re.match(pattern, cleaned_postcode):
        raise serializers.ValidationError(
            "Invalid UK postcode format. The postcode should have the format: 'SW1A0NY', 'W1J6LE', 'EC2R7DG'."
        )

    return value
class CustomerSerializer(serializers.ModelSerializer):
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
        required=True,
        style={
            "input_type": "text",
            "autocomplete": "off",
            "autofocus": False,
            "base_template": 'custom_input.html'
        }
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
        
        
    
class BillingAddressSerializer(serializers.ModelSerializer):
    vat_number = serializers.CharField(
        label='Vat Number',
        required=True,
        style={
            'base_template': 'custom_input.html'
        },
    )
    pan_number = serializers.CharField(
        label='PAN Number',
        required=True,
        style={
            'base_template': 'custom_input.html'
        },
    )
    place_to_supply = serializers.CharField(
        label='Place To Supply',
        required=False,
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
        # Custom validation for PAN number format (National Insurance Number in the UK)
        if not re.match(r'^[A-Z]{2}\d{6}[A-Z]$', value):
            raise serializers.ValidationError("Invalid PAN number format. It should consist of two letters, six digits, and a final letter (e.g., AB123456C).")
        return value
    
    class Meta:
        model = BillingAddress
        fields = ['vat_number', 'pan_number', 'place_to_supply', 'tax_preference', 'address',
                  'country', 'town', 'county', 'post_code']
        

class SiteAddressSerializer(serializers.ModelSerializer):
    site_name = serializers.CharField(
        max_length=255,
        required=True,
        style={
            'base_template': 'custom_fullwidth_input.html'
        },
        
    )
    address = serializers.CharField(
        max_length=255,
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