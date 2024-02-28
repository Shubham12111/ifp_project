from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.validators import RegexValidator
from infinity_fire_solutions.aws_helper import *
from infinity_fire_solutions.custom_form_validation import *
from infinity_fire_solutions.utils import generate_random_password
from authentication.models import CUSTOMER_TYPES, User
from authentication.serializers import SignupSerializer, UserRole
from rest_framework.validators import UniqueValidator, UniqueTogetherValidator
from .models import *
import re
from customer_management.constants import POST_CODE_LIST
import uuid
from customer_management.models import SiteAddress
from django.db import transaction
from django.core.exceptions import ValidationError
from decimal import Decimal

from requirement_management.models import *
from infinity_fire_solutions.validators import CustomFileValidator

from django.shortcuts import get_object_or_404

# Define a serializer for ContactCustomer model
class ContactCustomerSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = CustomerMeta
        fields = (
            'company_name', 'company_registration_number', 
            'registered_address', 'registered_town', 'registered_county', 'registered_country',  'registered_post_code',
            'email', 'main_telephone_number'
        )
    
    def get_or_create_user(self, attr):
        """
        Get or create a user based on the provided attributes.
        
        Args:
            attr (dict): A dictionary containing user attributes.

        Returns:
            User: The created or existing user object.

        Raises:
            serializers.ValidationError: If unable to create a customer with the provided name.
        """
        # Generate a unique email based on company name and current timestamp
        company_name = attr.get('company_name', '')
        currenttimestamp = int(datetime.now().timestamp())
        email = f'{"".join(company_name.split()).lower()}_{currenttimestamp}@infinityfireprevention.com'
        
        # Generate a random password
        password = generate_random_password()

        last_name = 'infinity'

        # Split company name to first name and last name
        if len(company_name.split()) > 1:
            first_name = company_name.split()[0].lower()
            last_name = ''.join(company_name.split()[1:]).lower()
        else:
            first_name = company_name.lower()
        
        # Create user data for serializer
        data = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'password': password,
            'password2': password
        }

        # Validate and save user data using SignupSerializer
        serializer = SignupSerializer(data=data)
        if not serializer.is_valid():
            raise serializers.ValidationError({
                'company_name': ['Unable to create Customer with this name please choose a different name and try again.']
            })
        
        # Save user with inactive status and company name
        user = serializer.save()
        user.is_active = False
        user.company_name = company_name
        
        # Assign 'Customer' role to the user
        customer_role = UserRole.objects.filter(name__icontains='customer').first()
        if customer_role:
            user.roles = customer_role
        else:
            customer_role = UserRole.objects.create(name='Customer')
            user.roles = customer_role
        
        user.save()

        return user

    def validate(self, attr):
        """
        Validate the attributes.
        
        Args:
            attr (dict): A dictionary containing user attributes.

        Returns:
            dict: The validated attributes.

        """
        # Call the base class validate method
        attr = super().validate(attr)

        # If instance exists, assign user_id or create a new user
        if self.instance:
            if not self.instance.user_id:
                attr['user_id'] = self.get_or_create_user(attr)
            else:
                attr['user_id'] = self.instance.user_id
        else:
            attr['user_id'] = self.get_or_create_user(attr)
        
        return attr


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
    company_name = serializers.CharField(
        label=_('Company Name'),
        max_length=100,
        min_length=3,
        required=True,
        style={
            "input_type": "text",
            "autocomplete": "off",
            "autofocus": False,
            "base_template": 'custom_input.html',
            'custom_class': 'col-4'
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
        default='public sector-NHS',
        style={
            'base_template': 'custom_select.html',
            'custom_class': 'col-4'
        },
    )
    
    company_registration_number = serializers.CharField(
        label=_('Company Registration Number'),
        max_length=100,
        min_length=3,
        required=True,
        style={
            "input_type": "text",
            "autocomplete": "off",
            "autofocus": False,
            "base_template": 'custom_input.html',
            'custom_class': 'col-4'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Company Registration Number is required.",
            "min_length": "Company Registration Number must consist of at least 3 characters."
        },
        validators=[RegexValidator(regex=r'^[a-zA-Z0-9]+(?:[-_][a-zA-Z0-9]+)*$')] 
    )
    
    registered_address = serializers.CharField(
        label=_('Registered Address'),
        max_length=255,
        min_length=5,
        required=True,
        style={
            'base_template': 'custom_input.html',
            'custom_class': 'col-4'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Address is required.",
        },
    )
    registered_town = serializers.CharField(
        label=_('Registered Town'),
        style={
            'base_template': 'custom_input.html',
            'custom_class': 'col-4'
        },
    )
    registered_county = serializers.CharField(
        label=_('Registered County'),
        style={
            'base_template': 'custom_input.html',
            'custom_class': 'col-4'
        },
    )
    registered_country = serializers.CharField(
        label=_('Registered Country'),
        style={
            'base_template': 'custom_input.html',
            'custom_class': 'col-6'
        },
    )
    registered_post_code = serializers.ChoiceField(
        label=_('Registered Post Code'),
        required = True,
        choices=POST_CODE_LIST,

        style={
            'base_template': 'custom_select_without_search.html',
            'custom_class': 'col-6'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Post Code is required.",
        },
        # validators=[validate_uk_postcode] 
    )

    trading_address = serializers.CharField(
        label=_('Trading Address'),
        max_length=255,
        min_length=5,
        required=True,
        style={
            'base_template': 'custom_input.html',
            'custom_class': 'col-4'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Address is required.",
        },
    )
    trading_town = serializers.CharField(
        label=_('Trading Town'),
        style={
            'base_template': 'custom_input.html',
            'custom_class': 'col-4'
        },
    )
    trading_county = serializers.CharField(
        label=_('Trading County'),
        style={
            'base_template': 'custom_input.html',
            'custom_class': 'col-4'
        },
    )
    trading_country = serializers.CharField(
        label=_('Trading Country'),
        style={
            'base_template': 'custom_input.html',
            'custom_class': 'col-6'
        },
    )
    trading_post_code = serializers.ChoiceField(
        label=_('Trading Post Code'),
        required = True,
        choices=POST_CODE_LIST,

        style={
            'base_template': 'custom_select_without_search.html',
            'custom_class': 'col-6'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Post Code is required.",
        },
        # validators=[validate_uk_postcode] 
    )


    utr_number = serializers.CharField(
        label=_('UTR Number'),
        max_length=100,
        min_length=3,
        required=True,
        style={
            "input_type": "text",
            "autocomplete": "off",
            "autofocus": False,
            "base_template": 'custom_input.html',
            'custom_class': 'col-4'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "UTR Number is required.",
            "min_length": "UTR Number must consist of at least 3 characters."
        },
        validators=[RegexValidator(regex=r'^[A-Z]+[0-9]+$')] 
    )
    
    email = serializers.EmailField(
        label=_('Email Address'),
        validators=[UniqueValidator(queryset=User.objects.all(), message="Email already exists. Please use a different email.")],
        required=True,
        max_length=100,
        style={
            "input_type": "email",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
            'base_template': 'customer_email.html',
            'custom_class': 'col-4'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Email Address is required.",
        },
    )

    main_telephone_number = serializers.CharField(
        label=_('Main Telephone Number'),
        max_length=14,
        min_length=10,
        required=True,
        allow_null=True,
        allow_blank=True,
        style={
            'base_template': 'custom_input.html',
            'custom_class': 'col-4'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Main Telephone Number field is required.",
            "max_length": "Invalid Main Telephone Number and max limit should be 14.",
            "min_length": "Invalid Main Telephone Number and min limit should be 10."
        },
        validators=[validate_phone_number] 
    )
    

    class Meta:
        model = CustomerMeta
        fields = (
            'company_name', 'customer_type', 'company_registration_number', 
            'registered_address', 'registered_town', 'registered_county', 'registered_country',  'registered_post_code',
            'trading_address', 'trading_town', 'trading_county', 'trading_country',  'trading_post_code',
            'utr_number', 'email', 'main_telephone_number')
    
    def validate_company_name(self, value):
        """
        Validates the uniqueness of the company name.
        
        Args:
            value (str): The company name to be validated.
            
        Returns:
            str: The validated company name.
        
        Raises:
            serializers.ValidationError: If the company name is already in use.
        """
        
        # Query the database for existing customers with the same company name
        customers = CustomerMeta.objects.filter(company_name=value).all()

        # Check if creating a new instance and the company name already exists
        if not self.instance and customers:
            raise serializers.ValidationError('Company Name is already in use.')
        
        # Check if updating an existing instance and the company name is already in use by another instance
        if self.instance and [customer for customer in customers if customer.id != self.instance.id]:
            raise serializers.ValidationError('Company Name is already in use.')
        
        return value

    def get_or_create_user(self, attr):
        """
        Get or create a user based on the provided attributes.
        
        Args:
            attr (dict): A dictionary containing user attributes.

        Returns:
            User: The created or existing user object.

        Raises:
            serializers.ValidationError: If unable to create a customer with the provided name.
        """
        # Generate a unique email based on company name and current timestamp
        company_name = attr.get('company_name', '')
        currenttimestamp = int(datetime.now().timestamp())
        email = f'{"".join(company_name.split()).lower()}_{currenttimestamp}@infinityfireprevention.com'
        
        # Generate a random password
        password = generate_random_password()

        last_name = 'infinity'

        # Split company name to first name and last name
        if len(company_name.split()) > 1:
            first_name = company_name.split()[0].lower()
            last_name = ''.join(company_name.split()[1:]).lower()
        else:
            first_name = company_name.lower()
        
        # Create user data for serializer
        data = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'password': password,
            'password2': password
        }

        # Validate and save user data using SignupSerializer
        serializer = SignupSerializer(data=data)
        if not serializer.is_valid():
            raise serializers.ValidationError({
                'company_name': ['Unable to create Customer with this name please choose a different name and try again.']
            })
        
        # Save user with inactive status and company name
        user = serializer.save()
        user.is_active = False
        user.company_name = company_name
        
        # Assign 'Customer' role to the user
        customer_role = UserRole.objects.filter(name__icontains='customer').first()
        if customer_role:
            user.roles = customer_role
        else:
            customer_role = UserRole.objects.create(name='Customer')
            user.roles = customer_role
        
        user.save()

        return user

    def validate(self, attr):
        """
        Validate the attributes.
        
        Args:
            attr (dict): A dictionary containing user attributes.

        Returns:
            dict: The validated attributes.

        """
        # Call the base class validate method
        attr = super().validate(attr)

        # If instance exists, assign user_id or create a new user
        if self.instance:
            if not self.instance.user_id:
                attr['user_id'] = self.get_or_create_user(attr)
            else:
                attr['user_id'] = self.instance.user_id
        else:
            attr['user_id'] = self.get_or_create_user(attr)

        return attr
    
    def create(self, validated_data):
        return super().create(validated_data)

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
    contact_email = serializers.EmailField(
        label=_('Accounts Email Address'),
        validators=[UniqueValidator(queryset=BillingAddress.objects.all(), message="Email already exists. Please use a different email.")],
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

    contact_tel_no = serializers.CharField(
        label=_('Accounts Contact Number'),
        max_length=14,
        min_length=10,
        required=True,
        allow_null=True,
        allow_blank=True,
        style={
            'base_template': 'custom_input.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Phone number field is required.",
            "max_length": "Invalid Phone number and max limit should be 14.",
            "min_length": "Invalid Phone number and min limit should be 10."
        },
        validators=[validate_phone_number]
    )
   
    address = serializers.CharField(
        label=_('Billing Address'),
        max_length=255,
        min_length=5,
        required=False,
        allow_blank=True,
        allow_null=True,
        style={
            'base_template': 'custom_input.html',
            'custom_class': 'col-4'
        },
    )
    
    country = serializers.CharField(
        label=_('Country'),
        style={
            'base_template': 'custom_input.html',
            'custom_class': 'col-6'
        },
    )
    
    town = serializers.CharField(
        label=_('Town'),
        style={
            'base_template': 'custom_input.html',
            'custom_class': 'col-4'
        },
    )
    
    county = serializers.CharField(
        label=_('County'),
        style={
            'base_template': 'custom_input.html',
            'custom_class': 'col-4'
        },
    )
    
    post_code = serializers.ChoiceField(
        label=_('Post Code'),
        required = True,
        choices=POST_CODE_LIST,

        style={
            'base_template': 'custom_select_without_search.html',
            'custom_class': 'col-6'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Post Code is required.",
        },
    )

    vat_number = serializers.CharField(
        label=_('VAT Number'),
        required=True,
        style={
            'base_template': 'custom_input.html',
            "placeholder":"Vat Number must be of 9 digits"
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
            'base_template': 'custom_select_without_search.html',
            'custom_class': 'col-6'
        },
    )

    payment_terms = serializers.ChoiceField(
        label=_('Payment Terms'),
        required = True,
        choices=PAYMENT_TERMS_CHOICES,
        # default='30 days',

        style={
            'base_template': 'custom_select_without_search.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Payment Terms is required.",
        },
        # validators=[validate_uk_postcode] 
    )

    purchase_order_required = serializers.BooleanField(
        label=_('Purchase Order Required'),
        default=False,
        style={
            'custom_class': 'ms-3',
            'input_type':'checkbox',
            'base_template': 'custom_boolean_input.html'
        },
    )
    
    CIS = serializers.BooleanField(
        label=('CIS'),
        default=False,
        style={
            'custom_class': 'ms-3',
            'input_type':'checkbox',
            'base_template': 'custom_boolean_input.html'
        },
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
        fields = ['vat_number','payment_terms','CIS','address', 'town', 'county', 'country','post_code','contact_email','contact_tel_no', 'purchase_order_required', 'tax_preference' ]
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
            'base_template': 'custom_input.html',
            'custom_class': 'col-4'
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
            'base_template': 'custom_input.html',
            'custom_class': 'col-4'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Address is required.",
        },
    )
    
    country = serializers.CharField(
        label=_('Country'),
        style={
            'base_template': 'custom_input.html'
        },
    )
    
    town = serializers.CharField(
        label=_('Town'),
        style={
            'base_template': 'custom_input.html'
        },
    )
    
    county = serializers.CharField(
        label=_('County'),
        style={
            'base_template': 'custom_input.html'
        },
    )
    
    post_code = serializers.ChoiceField(
        label=_('Post Code'),
        required = True,
        choices=POST_CODE_LIST,

        style={
            'base_template': 'custom_select_without_search.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Post Code is required.",
        },
        # validators=[validate_uk_postcode] 
    )
    UPRN = serializers.CharField(
        label = _('UPRN'),
        style={
            'base_template': 'custom_input.html',
            'custom_class': 'col-4'
        },
    )

    full_address = serializers.SerializerMethodField()  # New field for combined address

    
    class Meta:
        model = SiteAddress
        fields = ['id', 'site_name', 'UPRN','address', 'country', 'town', 'county', 'post_code','full_address']

    def get_full_address(self, instance):
        # Create a dictionary with label names and corresponding values
        address_components = {
            'Country': instance.country if instance.country else '',
            'County': instance.county  if instance.county else '',
            'Town': instance.town if instance.town else '',
        }

        # Filter out empty values and create a string with labels and values
        formatted_address = ', '.join(f'{label} - {value}' for label, value in address_components.items() if value)

        return formatted_address


class ContactProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number']

    

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
        validators=[
            UniqueValidator(
                queryset=User.objects.all(), message="Email already exists. Please use a different email."
            )
        ],
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
        label=_('Phone Number'),
        max_length=14,
        min_length=10,
        required=True,
        allow_null=True,
        allow_blank=True,
        style={
            'base_template': 'custom_input.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Phone number field is required.",
            "max_length": "Invalid Phone number and max limit should be 14.",
            "min_length": "Invalid Phone number and min limit should be 10."
        },
        validators=[validate_phone_number]
    )

    job_role = serializers.CharField(
        label=_('Job Role'),
        required=True,
        allow_null=True,
        allow_blank=True,
        style={
            'base_template': 'custom_input.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Job Role field is required.",
        
        },
        validators=[validate_job_role]
    )
    
    class Meta:
        model = ContactPerson
        fields = ['first_name', 'last_name', 'email', 'phone_number','job_role']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields['email'].required = False
            self.fields['email'].style.update({'disabled': True})
    
    def to_representation(self, instance):
        ret = {
            'first_name': instance.user.first_name,
            'last_name': instance.user.last_name,
            'email': instance.user.email,
            'phone_number': instance.user.phone_number,
            'job_role': instance.job_role
        }
        return ret

    def validate_first_name(self, value):
        """
        Validate the first name field.

        Args:
            value (str): First name value.

        Returns:
            str: Validated first name.

        Raises:
            serializers.ValidationError: If the first name is invalid.
        """
        if not re.match(r'^[a-zA-Z\s]+$', value):
            raise serializers.ValidationError("Invalid First Name. Only alphabets and spaces are allowed.")

        if len(value) < 2:
            raise serializers.ValidationError("First Name should be at least 2 characters long.")

        return value

    def validate_last_name(self, value):
        """
        Validate the last name field.

        Args:
            value (str): Last name value.

        Returns:
            str: Validated last name.

        Raises:
            serializers.ValidationError: If the last name is invalid.
        """
        if not re.match(r'^[a-zA-Z\s]+$', value):
            raise serializers.ValidationError("Invalid Last Name. Only alphabets and spaces are allowed.")

        if len(value) < 2:
            raise serializers.ValidationError("Last Name should be at least 2 characters long.")

        return value
    
    def create(self, validated_data):
        """
        Method to create a new user with the provided validated data.

        Args:
            validated_data (dict): Validated data containing user information.

        Returns:
            User: Newly created user instance.

        Raises:
            None.
        """

        # get the role for the contact
        contact_role = UserRole.objects.filter(name='customer_contact').first()
        # if the role is not present create the role
        if not contact_role:
            contact_role = UserRole.objects.create(name='customer_contact')
        
        # Generate a random password for the user
        password = generate_random_password()
        
        # Extract user data from validated data and create a new user
        data = {
            'first_name': validated_data.pop('first_name', ''),
            'last_name': validated_data.pop('last_name', ''),
            'email': validated_data.pop('email', ''),
            'password': password
        }

        user = User.objects.create_user(**data)
        
        # Update additional user fields
        user.phone_number = validated_data.pop('phone_number', '')
        user.is_active = False
        user.roles = contact_role
        user.save()
        
        # Assign the newly created user to the validated data and call the superclass create method
        validated_data['user'] = user
        instance = super().create(validated_data)
        return instance
    
    def update(self, instance, validated_data):
        # Extract user data from validated data and create a new user
        data = {
            'first_name': validated_data.pop('first_name', ''),
            'last_name': validated_data.pop('last_name', ''),
            'phone_number': validated_data.pop('phone_number', '')
        }
        serializer = ContactProfileSerializer(data=data, instance=instance.user)
        serializer.is_valid()
        serializer.update(instance=instance.user, validated_data=serializer.validated_data)

        validated_data['user'] = instance.user
        instance = super().update(instance, validated_data)
        return instance
        
class PostCodeInfoSerializer(serializers.Serializer):
    post_code = serializers.CharField(max_length=255)
    town = serializers.CharField(max_length=255)
    county = serializers.CharField(max_length=255)
    country = serializers.CharField(max_length=255)




class SORSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        label=('Name'),
        max_length=225, 
        required=True, 
        style={
            'base_template': 'custom_input.html',
            'custom_class':'col-6'
        },
        error_messages={
            "required": "Item Name is required.",
            "blank":"Name is required.",
        },
    )
    description = serializers.CharField(
        max_length=1000, 
        required=True, 
        style={'base_template': 'rich_textarea.html', 'rows': 5},
        error_messages={
            "required": "Description is required.",
            "blank":"Description is required.",
        },
        validators=[validate_description]
    )
    
    
    category_id = serializers.PrimaryKeyRelatedField(
        label=('Category'),
        required=False,
        queryset=SORCategory.objects.all(),
        style={
            'base_template': 'custom_select.html',
            'custom_class':'col-6'
        },
    )

    price = serializers.DecimalField(
        label=('Price ( £ )'),
        max_digits=10,
        decimal_places=2,
        required=True,
        style={
            'base_template': 'custom_input.html',
            'custom_class':'col-6'
        },
        error_messages={
            "required": "Price is required.",
            "invalid": "Price is invalid.",  
            "blank":"Price is required.", 
            "max_length": "Invalid price and max limit should be 10.",
        },
    )
    
    reference_number = serializers.CharField(
        label=('SOR Code'),
        max_length=50,
        required=True,
        style={
            'base_template': 'custom_input.html',
            'custom_class':'col-6'
        },
        error_messages={
            "required": "Reference Number is required.",
            "invalid": "Reference Number is invalid.",  
            "blank":"Reference Number is required.", 
        },
    )
    units = serializers.ChoiceField(
        label=('Units'),
        choices=UNIT_CHOICES, 
        required=True,
        style={
            'base_template': 'custom_select.html',
            'custom_class':'col-6 units'
        },
        error_messages={
            "required": "Units is required.",
            "invalid": "Units is invalid.",  
            "blank":"Units is required.", 
        },
    )
    
    file_list = serializers.ListField(
        child=serializers.FileField(
            allow_empty_file=False,
            validators=[CustomFileValidator()],
        ),
        label=('Documents'),  # Adjust the label as needed
        required=False,
        initial=[],
        style={
            "input_type": "file",
            "class": "form-control",
            "autofocus": False,
            "autocomplete": "off",
            'base_template': 'custom_multiple_file.html',
            'help_text': True,
            'multiple': True,
            'accept': ".png, .jpg, .jpeg,",
            'allow_null': True,  # Allow None values
        },
        help_text=('Supported file extensions: ' + ', '.join(settings.SUPPORTED_EXTENSIONS))
        )
        
    class Meta:
        model = SORItem
        fields = ['name','reference_number','category_id','price', 'description','units','file_list']

        
    def validate_price(self, value):
        # Ensure that the price is not empty or None
        if value is None:
            raise ValidationError("Price is required.")

        # Ensure that the price is a valid Decimal with 2 decimal places
        if not isinstance(value, Decimal) and not isinstance(value, int):
            raise ValidationError("Price is invalid.")

        # Ensure that the price is not negative

        if value <=0:

            raise ValidationError("Price cannot be negative or zero")

        # Ensure that the price has at most 10 digits in total
        if len(str(value)) > 10:
            raise ValidationError("Invalid price, max limit should be 10 digits.")

        # Ensure that the price has at most 2 decimal places
        if value.as_tuple().exponent < -2:
            raise ValidationError("Price can have at most 2 decimal places.")

        return value

    def validate_item_name(self, value):
        # Check for minimum length of 3 characters
        if len(value) < 3:
            raise serializers.ValidationError("Item Name must be at least 3 characters long.")
         # Check if the value consists entirely of digits (integers)
        if value.isdigit():
            raise serializers.ValidationError("Item Name cannot consist of only integers.")

        # Check for alphanumeric characters and spaces
        if not re.match(r'^[a-zA-Z0-9\s]*$', value):
            raise serializers.ValidationError("Item Name can only contain alphanumeric characters and spaces.")

        return value


    def validate_reference_number(self, value):
        """
        Validate that the reference number (SOR code) is unique for the given customer.
        """
        instance = self.instance
        customer_id = self.context.get('customer_id')

        # If updating an existing instance, exclude the current instance from the uniqueness check
        queryset = SORItem.objects.filter(reference_number=value, customer_id=customer_id)
        if instance:
            queryset = queryset.exclude(id=instance.id)

        if queryset.exists():
            raise serializers.ValidationError("This SOR code is already in use for this customer.")

        return value
    
    def create(self, validated_data):
        # Pop the 'file_list' field from validated_data
        file_list = validated_data.pop('file_list', None)
        # Create a new instance of Requirement with other fields from validated_data
        instance = SORItem.objects.create(**validated_data)

        if file_list and len(file_list) > 0:
            for file in file_list:
                # Generate a unique filename for each file
                unique_filename = f"{str(uuid.uuid4())}_{file.name}"
                upload_file_to_s3(unique_filename, file, f'fra/sor/{instance.id}')
                file_path = f'fra/sor/{instance.id}/{unique_filename}'
                
                # save the Product images
                SORItemImage.objects.create(
                sor_id = instance,
                image_path=file_path,
                )

        instance.save()
        return instance
    
    def update(self, instance, validated_data):
        file_list = validated_data.pop('file_list', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        with transaction.atomic():
            instance.save()

            # Update associated documents if file_list is provided
            if file_list and len(file_list) > 0:
                
                for file in file_list:
                    unique_filename = f"{str(uuid.uuid4())}_{file.name}"
                    upload_file_to_s3(unique_filename, file, f'fra/sor/{instance.id}')
                    file_path = f'fra/sor/{instance.id}/{unique_filename}'
                
                    SORItemImage.objects.create(
                        sor_id=instance,
                        image_path=file_path,
                )
        
        return instance
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)

        document_paths = []
        if hasattr(instance, 'soritemimage_set'):  # Using 'itemimage_set' for images
            for document in SORItemImage.objects.filter(sor_id=instance):
                document_paths.append({
                    'presigned_url': generate_presigned_url(document.image_path),
                    'filename': document.image_path.split('/')[-1],
                    'id': document.id  #  document ID
                })

        
        representation['document_paths'] = document_paths
        return representation

class BulkSorAddSerializer(serializers.ModelSerializer):
    
    description = serializers.CharField(
        max_length=1000,
        required=True,
        validators=[validate_description],
    )
    category_id = serializers.CharField(
        required=True, 
        allow_null=False, 
        allow_blank=False
    )
    price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True,
    )
    units = serializers.ChoiceField(
        choices=UNIT_CHOICES,
        required=True,
    )
    customer_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=False, roles__name='Customer').all(),
        required=True
    )

    class Meta:
        model = SORItem
        fields = ['customer_id', 'name', 'reference_number', 'category_id', 'price', 'description', 'units']
        validators = [
            UniqueTogetherValidator(
                queryset=SORItem.objects.all(),
                fields=['reference_number', 'customer_id'],
                message='The combination of reference_number, and customer must be unique.'
            )
        ]

    def validate_price(self, value):
        # Ensure that the price is not empty or None
        if value is None:
            raise ValidationError("Price is required.")

        # Ensure that the price is a valid Decimal with 2 decimal places
        if not isinstance(value, Decimal) and not isinstance(value, int):
            raise ValidationError("Price is invalid.")

        # Ensure that the price is not negative

        if value <=0:

            raise ValidationError("Price cannot be negative or zero")

        # Ensure that the price has at most 10 digits in total
        if len(str(value)) > 10:
            raise ValidationError("Invalid price, max limit should be 10 digits.")

        # Ensure that the price has at most 2 decimal places
        if value.as_tuple().exponent < -2:
            raise ValidationError("Price can have at most 2 decimal places.")

        return value

    def validate_name(self, value):
        # Check for minimum length of 3 characters
        if len(value) < 3:
            raise serializers.ValidationError("Item Name must be at least 3 characters long.")
         # Check if the value consists entirely of digits (integers)
        if value.isdigit():
            raise serializers.ValidationError("Item Name cannot consist of only integers.")

        # Check for alphanumeric characters and spaces
        if not re.match(r'^[a-zA-Z0-9\s]*$', value):
            raise serializers.ValidationError("Item Name can only contain alphanumeric characters and spaces.")

        return value

    def validate_category_id(self, value):
        try:
            category_instance = get_object_or_404(SORCategory, name=value)
            return category_instance
        except Exception as e:
            raise serializers.ValidationError(f"Category with name '{value}' does not exist.")