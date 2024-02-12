from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from infinity_fire_solutions.aws_helper import *
from infinity_fire_solutions.custom_form_validation import *
from authentication.models import CUSTOMER_TYPES, User
from rest_framework.validators import UniqueValidator
from .models import *
import re
from customer_management.constants import POST_CODE_LIST
import uuid
from customer_management.models import SiteAddress
from django.db import transaction
from django.core.exceptions import ValidationError
from decimal import Decimal

from requirement_management.models import *
from requirement_management.serializers import CustomFileValidator

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
        default='public sector-NHS',
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
    
    contact_name = serializers.CharField(
        label=_('Contact Name'),
        style={
            'base_template': 'custom_input.html'
        },
    )
    contact_email = serializers.EmailField(
        label=_('Contact Email'),
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
        label=_('Contact Phone Number'),
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
        label=_('Address'),
        max_length=255,
        min_length=5,
        required=False,
        allow_blank=True,
        allow_null=True,
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
            'base_template': 'custom_select.html'
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
            'base_template': 'custom_select.html',
            'custom_class': 'col-6'
        },
    )

    payment_terms = serializers.ChoiceField(
        label=_('Payment Terms'),
        required = True,
        choices=PAYMENT_TERMS_CHOICES,
        # default='30 days',

        style={
            'base_template': 'custom_select.html'
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
        fields = ['contact_name','contact_email','contact_tel_no','payment_terms', 'address', 'country', 'town', 'county', 'post_code','vat_number', 'tax_preference', 'purchase_order_required']

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
            'base_template': 'custom_select.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Post Code is required.",
        },
        # validators=[validate_uk_postcode] 
    )
    full_address = serializers.SerializerMethodField()  # New field for combined address

    
    class Meta:
        model = SiteAddress
        fields = ['id', 'site_name', 'address', 'country', 'town', 'county', 'post_code','full_address']

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
    
    class Meta:
        model = ContactPerson
        fields = ['first_name', 'last_name', 'email', 'phone_number']
        
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
