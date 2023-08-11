from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from infinity_fire_solutions.custom_form_validation import *

from .models import *
import re



class VendorSerializer(serializers.ModelSerializer):
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
        validators=[UniqueValidator(queryset=Vendor.objects.all(), message="Email already exists. Please use a different email.")],
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
        required=True,
        style={
            'base_template': 'custom_input.html',
            "required": True,
            "autocomplete": "off",
            "autofocus": False
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Phone number is required."
        },
        validators=[validate_phone_number],

    )
    company = serializers.CharField(
        label=('Company'),
        max_length=100,
        required=False,
        style={
            "input_type": "text",
            "autocomplete": "off",
            "autofocus": False,
            "base_template": 'custom_input.html'
        }
    )
    class Meta:
        model = Vendor
        fields = ('first_name','last_name','email','phone_number','company')


    def validate_first_name(self, value):
        if not re.match(r'^[a-zA-Z\s]+$', value):
            raise serializers.ValidationError("Invalid First Name. Only alphabets and spaces are allowed.")

        if len(value) < 2:
            raise serializers.ValidationError("First Name should be at least 2 characters long.")

        return value

    def validate_last_name(self, value):
        if not re.match(r'^[a-zA-Z\s]+$', value):
            raise serializers.ValidationError("Invalid Last Name. Only alphabets and spaces are allowed.")

        if len(value) < 2:
            raise serializers.ValidationError("Last Name should be at least 2 characters long.")

        return value


class BillingDetailSerializer(serializers.ModelSerializer):

    vat_number = serializers.CharField(
        label='VAT Number',
        max_length=20,
        required=True,
        style={
           "input_type": "text",
            "autocomplete": "off",
            "autofocus": False,
            "base_template": 'custom_input.html'
        },
    )
    pan_number = serializers.CharField(
        label='PAN Number',
        max_length=20,
        required=True,
        style={
           "input_type": "text",
            "autocomplete": "off",
            "autofocus": False,
            "base_template": 'custom_input.html'
        },
    )
    tax_preference = serializers.ChoiceField(
        label='Tax Preferences',
        choices= TAX_PREFERENCE_CHOICES,
        required=False,
        style={
            'base_template': 'custom_select.html',
            'custom_class': 'col-6'
        },
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
        label=('Post Code'),
        max_length=7,
        required=False,
        style={
            "input_type": "text",
            "autofocus": False,
            "autocomplete": "off",
            'base_template': 'custom_input.html'
        },

        validators=[validate_uk_postcode]

    )
    vendor_status = serializers.ChoiceField(
        label='Vendor Status',
        choices=VENDOR_STATUS_CHOICES,
        required=False,
        style={
            'base_template': 'custom_select.html',
            'custom_class': 'col-6'
        },
    )
        
    class Meta:
        model = Vendor 
        fields = ('vat_number','pan_number','tax_preference','vendor_status','address','town','county','country','post_code')

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


    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Check if the representation is empty (no records found)
        if not any(representation.values()):
            representation = {'message': 'No records found for this vendor.'}
        else:
            # Remove None values from the representation
            representation = {key: value for key, value in representation.items() if value is not None}

        return representation

    

class VendorContactPersonSerializer(serializers.ModelSerializer):

    salutation = serializers.ChoiceField(
        label=('Salutation '),
        required=True,
        choices= SALUTATION_CHOICES,
        style={
            'base_template': 'custom_select.html',
            'custom_class': 'col-6'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Salutation is required.",
        },

    )

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
        label=('Phone'),
        max_length=14,
        min_length=10,
        required= True,
        style={
            "input_type": "text",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
            "base_template": 'custom_input.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Phone number field is required.",
            "max_length": "Invalid Phone number and max limit should be 14.",
            "min_length": "Invalid Phone number and min limit should be 10."
        },
        validators=[validate_phone_number]
    )

    class Meta:
        model = VendorContactPerson
        fields = ['salutation','first_name' ,'last_name','email', 'phone_number']



class VendorRemarkSerializer(serializers.ModelSerializer):

    remarks = serializers.CharField(
        label=('Remarks '),
        required=True,
        max_length=255,
        style={
           'base_template': 'rich_textarea.html',
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Remarks is required.",
        },
         validators=[validate_remarks]
    )
    class Meta:
        model = Vendor
        fields = ['remarks',]



