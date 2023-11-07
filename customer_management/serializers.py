from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from infinity_fire_solutions.aws_helper import *
from infinity_fire_solutions.custom_form_validation import *
from authentication.models import CUSTOMER_TYPES, User
from rest_framework.validators import UniqueValidator
from .models import *
import re

# Define a serializer for ContactCustomer model
class ContactCustomerSerializer(serializers.ModelSerializer):
    """
    Serializer for ContactCustomer model.

    This serializer defines the fields and their characteristics for ContactCustomer objects.

    Attributes:
        first_name (serializers.CharField): Field for first name.
        last_name (serializers.CharField): Field for last name.
        email (serializers.EmailField): Field for email.
        phone_number (serializers.CharField): Field for phone number.
        company_name (serializers.CharField): Field for company name.

    Note:
        Additional validation and error messages are defined for each field.
    """
    
    first_name = serializers.CharField(
        label=_('First Name'),
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
        label=_('Last Name'),
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
        label=_('Email'),
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
    def validate_phone_number(value):
        if not value:
            return  # Allow empty values
        if not (value.startswith("+0") and len(value) == 13) and not (value.startswith("+44") and len(value) == 14):
            raise serializers.ValidationError(_("Phone number must start with '+0' and have 11 digits, or start with '+44' and have 12 digits."))
    phone_number = serializers.CharField(
        label=_('Phone Number'),
        max_length=14,
        min_length=10,
        required=False,
        allow_null=True,
        allow_blank=True,
        style={
            'base_template': 'custom_input.html'
        },
        validators=[validate_phone_number] 
    )
    
    company_name = serializers.CharField(
        label=_('Company Name'),
        max_length=100,
        min_length=3,
        required=False,
    )
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'company_name', 'phone_number')

# Define a serializer for Customer model
class CustomerSerializer(serializers.ModelSerializer):
    """
    Serializer for Customer model.

    This serializer defines the fields and their characteristics for Customer objects.

    Attributes:
        first_name (serializers.CharField): Field for first name.
        last_name (serializers.CharField): Field for last name.
        email (serializers.EmailField): Field for email.
        phone_number (serializers.CharField): Field for phone number.
        company_name (serializers.CharField): Field for company name.
        customer_type (serializers.ChoiceField): Field for customer type.

    Note:
        Additional validation and error messages are defined for each field.
    """
    
    first_name = serializers.CharField(
        label=_('First Name'),
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
        label=_('Last Name'),
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
        label=_('Email'),
        validators=[UniqueValidator(queryset=User.objects.all(), message="Email already exists. Please use a different email.")],
        required=True,
        max_length=100,
        style={
            "input_type": "email",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
            'base_template': 'customer_email.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Email is required.",
        },
    )
    def validate_phone_number(value):
        if not value:
            return  # Allow empty values
        if not (value.startswith("+0") and len(value) == 13) and not (value.startswith("+44") and len(value) == 14):
            raise serializers.ValidationError(_("Phone number must start with '+0' and have 11 digits, or start with '+44' and have 12 digits."))
    phone_number = serializers.CharField(
        label=_('Phone Number'),
        max_length=14,
        min_length=10,
        required=False,
        allow_null=True,
        allow_blank=True,
        style={
            'base_template': 'custom_input.html'
        },
        validators=[validate_phone_number] 
    )
    
    company_name = serializers.CharField(
        label=_('Company Name'),
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
        label=_('Customer Type'),
        choices=CUSTOMER_TYPES,
        default='individual',
        style={
            'base_template': 'custom_select.html',
            'custom_class': 'col-6'
        },
    )
   
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'company_name', 'phone_number', 'customer_type')

# Define a serializer for BillingAddress model
class BillingAddressSerializer(serializers.ModelSerializer):
    """
    Serializer for BillingAddress model.

    This serializer defines the fields and their characteristics for BillingAddress objects.

    Attributes:
        vat_number (serializers.CharField): Field for VAT number.
        tax_preference (serializers.ChoiceField): Field for tax preference.
        address (serializers.CharField): Field for address.
        country (serializers.PrimaryKeyRelatedField): Field for country.
        town (serializers.PrimaryKeyRelatedField): Field for town.
        county (serializers.PrimaryKeyRelatedField): Field for county.
        post_code (serializers.CharField): Field for postal code.

    Note:
        Additional validation and error messages are defined for some fields.
    """
    
    vat_number = serializers.CharField(
        label=_('VAT Number'),
        required=True,
        style={
            'base_template': 'custom_input.html'
        },

        error_messages={
            "required": "This field is required.",
            "blank": "Vat Number is required.",
        },

    )
    
    tax_preference = serializers.ChoiceField(
        label=_('Tax Preference'),
        choices=TAX_PREFERENCE_CHOICES,
        default='taxable',
        style={
            'base_template': 'custom_select.html',
            'custom_class': 'col-6'
        },
    )
   
    address = serializers.CharField(
        label=_('Address'),
        max_length=255,
        min_length=5,
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    
    country = serializers.PrimaryKeyRelatedField(
        label=_('Country'),
        queryset=Country.objects.all(),
        default=None,
        style={
            'base_template': 'custom_select.html'
        },
    )
    
    town = serializers.PrimaryKeyRelatedField(
        label=_('Town'),
        queryset=City.objects.all(),
        default=None,
        style={
            'base_template': 'custom_select.html'
        },
    )
    
    county = serializers.PrimaryKeyRelatedField(
        label=_('County'),
        queryset=Region.objects.all(),
        default=None,
        style={
            'base_template': 'custom_select.html'
        },
    )
    
    post_code = serializers.CharField(
        label=_('Post Code'),
        max_length=7,
        required=False,
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
    
    def validate_vat_number(self, value):
        """
        Custom validation for VAT number format (United Kingdom VAT number).

        Args:
            value (str): VAT number to be validated.

        Returns:
            str: Validated VAT number.

        Raises:
            serializers.ValidationError: If the VAT number is invalid.
        """
        if not re.match(r'^\d{9}$', value):
            raise serializers.ValidationError("Invalid VAT number format. It should be a 9-digit number.")
        if int(value) == 0:
            raise serializers.ValidationError("Only zeros are not allowed in VAT Number")
        return value
    
    class Meta:
        model = BillingAddress
        fields = ['vat_number', 'tax_preference', 'address', 'country', 'town', 'county', 'post_code']

# Define a serializer for SiteAddress model
class SiteAddressSerializer(serializers.ModelSerializer):
    """
    Serializer for SiteAddress model.

    This serializer defines the fields and their characteristics for SiteAddress objects.

    Attributes:
        site_name (serializers.CharField): Field for site name.
        address (serializers.CharField): Field for address.
        country (serializers.PrimaryKeyRelatedField): Field for country.
        town (serializers.PrimaryKeyRelatedField): Field for town.
        county (serializers.PrimaryKeyRelatedField): Field for county.
        post_code (serializers.CharField): Field for postal code.

    Note:
        Additional validation and error messages are defined for some fields.
    """
    
    site_name = serializers.CharField(
        label=_('Site Name'),
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
        label=_('Address'),
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
        label=_('Post Code'),
        max_length=7,
        required=True,
        allow_blank=False,
        allow_null=False,
        style={
            'base_template': 'custom_input.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Post Code is required.",
        },
        validators=[validate_uk_postcode] 
    )
    
    class Meta:
        model = SiteAddress
        fields = ['site_name', 'address', 'country', 'town', 'county', 'post_code']

# Define a serializer for ContactPerson model
class ContactPersonSerializer(serializers.ModelSerializer):
    """
    Serializer for ContactPerson model.

    This serializer defines the fields and their characteristics for ContactPerson objects.

    Attributes:
        first_name (serializers.CharField): Field for first name.
        last_name (serializers.CharField): Field for last name.
        email (serializers.EmailField): Field for email.
        phone_number (serializers.CharField): Field for phone number.

    Note:
        Additional validation and error messages are defined for each field.
    """
    
    first_name = serializers.CharField(
        label=_('First Name'),
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
        label=_('Last Name'),
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
        label=_('Email'),
        validators=[UniqueValidator(queryset=ContactPerson.objects.all(), message="Email already exists. Please use a different email.")],
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
    def validate_phone_number(value):
        if not value:
            return  # Allow empty values
        if not (value.startswith("+0") and len(value) == 13) and not (value.startswith("+44") and len(value) == 14):
            raise serializers.ValidationError(_("Phone number must start with '+0' and have 11 digits, or start with '+44' and have 12 digits."))

    phone_number = serializers.CharField(
        label=_('Phone Number'),
        max_length=14,
        min_length=10,
        required=False,
        allow_null=True,
        allow_blank=True,
        style={
            'base_template': 'custom_input.html'
        },
        validators=[validate_phone_number] 
    )
    
    class Meta:
        model = ContactPerson
        fields = ['first_name', 'last_name', 'email', 'phone_number']
