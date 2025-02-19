import uuid
from django.core.validators import RegexValidator

from rest_framework import serializers
from .models import Contact,ContactType,Conversation,ConversationType
from cities_light.models import City, Country, Region
from rest_framework.validators import UniqueValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _

from infinity_fire_solutions.aws_helper import *
from infinity_fire_solutions.custom_form_validation import *
import re
from bs4 import BeautifulSoup
from customer_management.constants import POST_CODE_LIST



# Custom validation function for validating file size
def validate_file_size(value):
    """
    Validate the file size is within the allowed limit.

    Parameters:
        value (File): The uploaded file.

    Raises:
        ValidationError: If the file size exceeds the maximum allowed size (5 MB).
    """
    # Maximum file size in bytes (5 MB)
    max_size = 5 * 1024 * 1024

    if value.size > max_size:
        raise ValidationError(_('File size must be up to 5 MB.'))

# Validator for checking the supported file extensions
file_extension_validator = FileExtensionValidator(
    allowed_extensions=settings.SUPPORTED_EXTENSIONS,
    message=_('Unsupported file extension. Please upload a valid file.'),
)

# Custom phone number validator to allow only digits
class PhoneNumberValidator(RegexValidator):
    regex = r'^\d+$'
    message = 'Phone number must contain only digits.'

class ContactSerializer(serializers.ModelSerializer):
    """
    Serializer for Contact model.
    """
    first_name = serializers.CharField(
        max_length=50,
        required= True,
        label='First Name',
        error_messages={
            "required": "This field is required.",
            "blank": "First Name is required.",
            "invalid": "First Name can only contain characters.",
        },
        style={
            "input_type": "text",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
            'base_template': 'custom_input.html'
        },
        validators=[validate_first_name] 
    )
    last_name = serializers.CharField(
        max_length=50,
        required= True,
        label='Last Name',
        error_messages={
            "required": "This field is required.",
            "blank": "Last Name is required.",
            "invalid": "Last Name can only contain characters.",
        },

        style={
            "input_type": "text",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
            'base_template': 'custom_input.html'
        },
        validators=[validate_last_name]
    )
    email = serializers.EmailField(
        label=('Email'),
        max_length=100,
        required= True,
        validators=[UniqueValidator(queryset=Contact.objects.all(), message="Email already exists. Please use a different email.")],
        style={
            "input_type": "email",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
            'base_template': 'custom_input.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Email field is required.",
        },
    )
    phone_number = serializers.CharField(
        label=('Phone'),
        max_length=14,
        min_length=10,
        required= True,
        allow_null=True,
        allow_blank=True,
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

    mobile_number = serializers.CharField(
        label=('Mobile Number'),
        max_length=14,
        min_length=10,
        required= False,
        allow_null=True,
        allow_blank=True,
        style={
            "input_type": "text",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
            "base_template": 'custom_input.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Mobile number field is required.",
            "max_length": "Invalid Mobile number and max limit should be 14.",
            "min_length": "Invalid Mobile number and min limit should be 10."
        },
        validators=[validate_phone_number]
    )
   

    job_title = serializers.CharField(
        label=('Job Title'),
        max_length=100,
        required= True,
        allow_null=True,
        allow_blank=True,
        style={
            "input_type": "text",
            "autofocus": False,
            "autocomplete": "off",
            "base_template": 'custom_input.html'
        }
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
        validators=[validate_company_name]
    )
    address = serializers.CharField(
        label=('Address'),
        max_length=100,
        min_length=5,
        required=False,
        allow_null=True,
        style={
            "input_type": "text",
            "autofocus": False,
            "autocomplete": "off",
            "base_template": 'custom_address.html'
        }
    )
    
    contact_type = serializers.SlugRelatedField(
        slug_field='name',
        label=('Contact Type'),
        required=True,
        queryset=ContactType.objects.all(),
        style={
            'base_template': 'custom_search.html',
            'custom_class': 'col-6 autocomplete',

        },
        error_messages={
            "required": "This field is required.",
            "blank": "Contact Type field cannot be blank.",
            "invalid": "Contact Type can only contain characters.",
            'does_not_exist': _('Contact type with {slug_name}, {value} does not exist.'),
            'null': "This field is required."
        },
    )
     
    country = serializers.CharField(
        label=_('Country'),
        max_length=50,
        min_length=5,
        required=False,
        style={
            'base_template': 'custom_input.html'
        },
    )
    town = serializers.CharField(
        label=_('Town'),
        max_length=50,
        min_length=5,
        required=False,
        style={
            'base_template': 'custom_input.html'
        },
    )
    county = serializers.CharField(
        label=_('County'),
        max_length=50,
        min_length=5,
        required=False,
        style={
            'base_template': 'custom_input.html'
        },
    )

    
    post_code = serializers.ChoiceField(
        label=('Post Code'),
        required=False,        
        choices=POST_CODE_LIST,
        style={
            "input_type": "text",
            "autofocus": False,
            "autocomplete": "off",
            'base_template': 'custom_select_without_search.html'
        },
          error_messages={
            "required": "This field is required.",
        },

        # validators=[validate_uk_postcode]

    )

    class Meta:
        model = Contact
        fields = ['first_name','last_name', 'email', 'phone_number','company_name', 'job_title','contact_type','mobile_number','address','town','county','country','post_code',]

        extra_kwargs={
            'name':{'required':True},
            'email':{'required':True},
            'phone_number':{'required':True},
            'contact_type':{'required':True}

        }

    def validate_first_name(self, value):
        """
    Validate the First Name field.
    
    Args:
        value (str): The value of the First Name field.

    Returns:
        str: The validated First Name value.

    Raises:
        serializers.ValidationError: If the First Name is invalid.

    """
        if not re.match(r'^[a-zA-Z\s]+$', value):
            raise serializers.ValidationError("Invalid First Name. Only alphabets and spaces are allowed.")

        if len(value) < 2:
            raise serializers.ValidationError("First Name should be at least 2 characters long.")

        return value

    def validate_last_name(self, value):
        """
    Validate the Last Name field.
    
    Args:
        value (str): The value of the Last Name field.

    Returns:
        str: The validated Last Name value.

    Raises:
        serializers.ValidationError: If the Last Name is invalid.

    """
        if not re.match(r'^[a-zA-Z\s]+$', value):
            raise serializers.ValidationError("Invalid Last Name. Only alphabets and spaces are allowed.")

        if len(value) < 2:
            raise serializers.ValidationError("Last Name should be at least 2 characters long.")

        return value
    

    def validate_contact_type(self, value):
        """
        Validate the Contact Type field.
        
        Args:
            value (str): The value of the Contact Type field.

        Returns:
            str: The validated Contact Type value.

        Raises:
            serializers.ValidationError: If the Contact Type is empty.
        """
        if not value:
            raise serializers.ValidationError("Contact Type cannot be empty.")
        return value
    


class ConversationViewSerializer(serializers.ModelSerializer):
    """
    Serializer for Conversation View.
    """
    presigned_url = serializers.SerializerMethodField()
    filename = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'conversation_type', 'title', 'message', 'document_path', 'created_at', 'presigned_url', 'filename']

    def get_presigned_url(self, conversation):
        """
        Get the pre-signed URL for the conversation document.

        Parameters:
            conversation (Conversation): The Conversation instance.

        Returns:
            str: The pre-signed URL for the document or None if it doesn't exist.
        """
        # Check if 'document_path' exists and generate the pre-signed URL
        if conversation.document_path:
            presigned_url = generate_presigned_url(conversation.document_path)
            return presigned_url
        else:
            return None

    def get_filename(self, conversation):
        """
        Get the filename from the 'document_path'.

        Parameters:
            conversation (Conversation): The Conversation instance.

        Returns:
            str: The filename or None if it doesn't exist.
        """
        # Extract the filename from the 'document_path'
        if conversation.document_path:
            return conversation.document_path.split('/')[-1]
        else:
            return None
        
    def to_representation(self, instance):
        """
        Serialize the Conversation instance.

        Parameters:
            instance (Conversation): The Conversation instance.

        Returns:
            dict: The serialized representation of the Conversation.
        """
        representation = super().to_representation(instance)

        if instance.conversation_type:
            representation['conversation_type'] = instance.conversation_type.name
        return representation

class ConversationSerializer(serializers.ModelSerializer):
    """
    Serializer for Conversation Model.
    """
    # Custom FileField for handling file uploads
    file = serializers.FileField(
    label=_('Document'),
    required=False,
    style={
        "input_type": "file",
        'accept': '.png, .jpg, .jpeg, .doc, .docx, .pdf, .txt, .zip, .csv , .xls, .xlsx ',
        "class": "form-control",
        "autofocus": False,
        "autocomplete": "off",
        'base_template': 'custom_file.html',
        'help_text':True,
    },
    validators=[file_extension_validator, validate_file_size],
    help_text=_('Supported file extensions: ' + ', '.join(settings.SUPPORTED_EXTENSIONS))
    )    
    # Custom CharField for the message with more rows (e.g., 5 rows)
    message = serializers.CharField(max_length=1000, 
                                    required=True, 
                                    style={'base_template': 'rich_textarea.html',
                                            'rows': 5},
                                    error_messages={
                                            "required": "This field is required.",
                                            "blank": "Message is required.",
                                        })

    
    title = serializers.CharField(
        max_length=250, 
        label=('Title'),
        required=True,
        style={
            "input_type": "input",
            "autofocus": False,
            "autocomplete": "off",
            'base_template': 'custom_fullwidth_input.html',
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Title is required.",
        },
    )
    conversation_type = serializers.PrimaryKeyRelatedField(
        label=('Conversation Type'),
        required=True,
        queryset=ConversationType.objects.all(),
        style=
        {
            'base_template': 'custom_select.html',
            'custom_class': 'col-12'
        },
    )
    class Meta:
        model = Conversation
        fields = [ 'conversation_type', 'title', 'message','file']
    

    def to_representation(self, instance):
        """
        Serialize the Conversation instance.

        Parameters:
            instance (Conversation): The Conversation instance.

        Returns:
            dict: The serialized representation of the Conversation.
        """
        representation = super().to_representation(instance)

        if instance.document_path:
            presigned_url = generate_presigned_url(instance.document_path)
            representation['presigned_url'] = presigned_url
            representation['filename'] = instance.document_path.split('/')[-1]

        if instance.id:
            representation['id'] = instance.id
        return representation

        
    def validate_message(self, value):
        """
        Custom validation for the message field to treat "<p><br></p>" as blank.

        Parameters:
            value (str): The value of the 'message' field.

        Returns:
            str: The validated 'message' field value.

        Raises:
            serializers.ValidationError: If the 'message' field is blank.
        """
        # Custom validation for the message field to treat <p><br></p> as blank
        soup = BeautifulSoup(value, 'html.parser')
        cleaned_comment = soup.get_text().strip()

        # Check if the cleaned comment consists only of whitespace characters
        if not cleaned_comment:
            raise serializers.ValidationError("Message is required.")

        if all(char.isspace() for char in cleaned_comment):
            raise serializers.ValidationError("Message cannot consist of only spaces and tabs.")

        return value

    def create(self, validated_data):
        """
        Create a new instance of Conversation with 'title', 'message', and handle file upload (if any).

        Parameters:
            validated_data (dict): The validated data for creating the Conversation instance.

        Returns:
            Conversation: The newly created Conversation instance.
        """
        # Pop the 'file' field from validated_data
        file = validated_data.pop('file', None)

        # Create a new instance of Conversation with 'title' and 'message'
        instance = Conversation.objects.create(**validated_data)

        if file:
            # Generate a unique filename
            unique_filename = f"{str(uuid.uuid4())}_{file.name}"
            upload_file_to_s3(unique_filename, file, 'contacts')
            instance.document_path = f'contacts/{unique_filename}'
            instance.save()

        return instance

    def update(self, instance, validated_data):
        """
        Update 'title', 'message', and handle file upload (if any) for the Conversation instance.

        Parameters:
            instance (Conversation): The existing Conversation instance to be updated.
            validated_data (dict): The validated data for updating the Conversation instance.

        Returns:
            Conversation: The updated Conversation instance.
        """
        # Update 'title' and 'message' fields
        instance.title = validated_data.get('title', instance.title)
        instance.message = validated_data.get('message', instance.message)
        instance.conversation_type = validated_data.get('conversation_type', instance.conversation_type)

        # Pop the 'file' field from validated_data
        file = validated_data.pop('file', None)

        if file:
            # If there was an existing document_path, delete the old file from S3
            if instance.document_path:
                s3_client.delete_object(Bucket=settings.AWS_BUCKET_NAME, Key=instance.document_path)

            # Generate a unique filename
            unique_filename = f"{str(uuid.uuid4())}_{file.name}"
            upload_file_to_s3(unique_filename, file, 'contacts')

            # Update the document_path with the new file path
            instance.document_path = f'contacts/{unique_filename}'

        instance.save()
        
        return instance
    
class PostCodeInfoSerializer(serializers.Serializer):
    post_code = serializers.CharField(max_length=255)
    town = serializers.CharField(max_length=255)
    county = serializers.CharField(max_length=255)
    country = serializers.CharField(max_length=255)
