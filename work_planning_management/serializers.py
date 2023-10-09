
from rest_framework import serializers
from requirement_management.models import Quotation  
from authentication.models import User
import re
import uuid
from django.db import transaction

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags
from django.core.validators import FileExtensionValidator

from rest_framework import serializers
from rest_framework.fields import empty

from collections import OrderedDict
from collections.abc import Mapping

from authentication.models import User
from infinity_fire_solutions.custom_form_validation import *
from infinity_fire_solutions.aws_helper import *
from customer_management.models import SiteAddress

from .models import *


class QuotationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quotation
        fields = '__all__'

class CustomFileValidator(FileExtensionValidator):
    def __init__(self, allowed_extensions=settings.IMAGE_SUPPORTED_EXTENSIONS, *args, **kwargs):
        super().__init__(allowed_extensions, *args, **kwargs)

    def __call__(self, value):
        extension_error = None
        size_error = None

        try:
            super().__call__(value)
        except ValidationError as e:
            extension_error = e.error_list[0].messages[0]

        max_size = 5 * 1024 * 1024  # 5MB in bytes
        if value.size > max_size:
            size_error = "File size must be no more than 5MB."

        if extension_error or size_error:
            errors = {}
            if extension_error:
                errors['extension'] = [extension_error]
            if size_error:
                errors['size'] = [size_error]
            raise serializers.ValidationError(errors)   
            
class CustomerSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'company_name')

class SiteAddressField(serializers.PrimaryKeyRelatedField):
    """
    Primary key related field for SiteAddress model.

    This field is used for relating SiteAddress model instances to other models.

    Methods:
        get_queryset: Get the queryset for SiteAddress instances.
    """
    def get_queryset(self):
        """
        Get the queryset for SiteAddress instances.

        Returns:
            QuerySet: A queryset of SiteAddress instances filtered by user_id.
        """
        # Get the user_id from the request's query parameters
        user_id = self.context['request'].parser_context['kwargs']['customer_id']
        # Filter the queryset based on the user_id
        if user_id:
            return SiteAddress.objects.filter(user_id=user_id)
        else:
            return SiteAddress.objects.none()

class STWRequirementSerializer(serializers.ModelSerializer):
    """
    Serializer for adding a new STW (Straight to work) requirement.

    Fields:
    - action: The STW action description.
    - RBNO: The RBNO (Reference Base Number) for the requirement.
    - UPRN: The UPRN (Unique Property Reference Number) for the requirement.
    - description: The STW description.
    - site_address: The site address.
    - status: The STW status.

    Validators:
    - RBNO uniqueness validator.
    - UPRN uniqueness validator.
    """
    action = serializers.CharField(
        label=('STW Action'),
        required=True, 
        style={'base_template': 'textarea.html'},
        error_messages={
            "required": "This field is required.",
            "blank": "Action is required.",
            "null": "Action is required."
        },
        validators=[action_description],
        
    )
    
    RBNO = serializers.CharField(
        label=('RBNO'),
        required=True,
        max_length=12,
        style={'base_template': 'custom_input.html'},
        error_messages={
            "required": "This field is required.",
            "blank": "RBNO is required.",
        },
    )
    
    UPRN = serializers.CharField(
        label=('UPRN'),
        required=True, 
        max_length=12,
        style={'base_template': 'custom_input.html'},
        error_messages={
            "required": "This field is required.",
            "blank": "UPRN is required.",
        },
    )

    description = serializers.CharField(
        label=('STW Description'),
        required=True, 
        style={'base_template': 'textarea.html'},
        error_messages={
            "required": "This field is required.",
            "blank": "Description is required.",
            "null": "Description is required."
        },
        validators=[validate_description],
        
    )
    
    site_address =SiteAddressField(
        label=('Site Address'),
        required = True,
        style={
            'base_template': 'custom_select.html',
            'custom_class':'col-6'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Site Address is required.",
            "incorrect_type":"Site Address is required.",
            "null": "Site Address is required."
        },
    )

    file_list = serializers.ListField(
        child=serializers.FileField(
            allow_empty_file=False,
            validators=[CustomFileValidator()],
        ),
        label=('Documents'),  # Adjust the label as needed
        required=False,
        write_only=True,
        initial=[],
        style={
            "input_type": "file",
            "class": "form-control",
            "autofocus": False,
            "autocomplete": "off",
            'base_template': 'custom_multiple_file.html',
            'help_text': True,
            'multiple': True,
            'accept': ','.join(settings.IMAGE_VIDEO_SUPPORTED_EXTENSIONS),
            'allow_null': True,
            'custom_class':'col-6'
        },
        help_text=('Supported file extensions: ' + ', '.join(settings.IMAGE_VIDEO_SUPPORTED_EXTENSIONS))
    )
    
    
    class Meta:
        model = STWRequirements
        fields = ('RBNO','UPRN','action','description', 'site_address','file_list')
    
    def validate_RBNO(self, value):
        """
        Validate the uniqueness of RBNO.

        Args:
            value (str): The RBNO value to be validated.

        Returns:
            str: The validated RBNO value.

        Raises:
            serializers.ValidationError: If the RBNO is not unique.
        """
        if not self.instance:
            if STWRequirements.objects.filter(RBNO=value).exists():
                raise serializers.ValidationError("RBNO already exists.")
        return value


    def validate_UPRN(self, value):
        """
        Validate the uniqueness of UPRN.

        Args:
            value (str): The UPRN value to be validated.

        Returns:
            str: The validated UPRN value.

        Raises:
            serializers.ValidationError: If the UPRN is not unique.
        """
        if not self.instance:
            # Check if an object with the same UPRN already exists
            if STWRequirements.objects.filter(UPRN=value).exists():
                raise serializers.ValidationError("UPRN already exists.")
        return value

    
    def get_initial(self):
        """
        Get the initial data for the serializer.

        Returns:
            OrderedDict: The initial data for the serializer.
        """
        
        fields = self.fields
        
        if hasattr(self, 'initial_data'):
            # initial_data may not be a valid type
            if not isinstance(self.initial_data, Mapping):
                return OrderedDict()

            if not self.instance:
                fields['file_list'].required = True
            
            return OrderedDict([
                (field_name, field.get_value(self.initial_data))
                for field_name, field in fields.items()
                if (field.get_value(self.initial_data) is not empty) and
                not field.read_only
            ])
        fields['file_list'].required = True
        
        return OrderedDict([
            (field.field_name, field.get_initial())
            for field in fields.values()
            if not field.read_only
        ])
    
    
    def create(self, validated_data):
        """
    Create a new STW requirement instance with associated files.

    Args:
        validated_data (dict): Validated data for creating a STW requirement instance.

    Returns:
        Requirement: The created STW requirement instance.
    """
        file_list = validated_data.pop('file_list', None)
        instance = STWRequirements.objects.create(**validated_data)

        if file_list and len(file_list) > 0:
            for file in file_list:
                unique_filename = f"{str(uuid.uuid4())}_{file.name}"
                try:
                    upload_file_to_s3(unique_filename, file, f'work_planning/{instance.id}')
                    file_path = f'work_planning/{instance.id}/{unique_filename}'
                    
                    document = STWAsset.objects.create(stw_id=instance, document_path=file_path)
                
                except Exception as e:
                    # Handle the exception (e.g., log the error) and decide what to do next
                    pass

        return instance
    
    def update(self, instance, validated_data):
        """
    Update an existing STW Requirement instance with associated files.

    Args:
        instance (Requirement): The existing STW Requirement instance to be updated.
        validated_data (dict): Validated data for updating the STW Requirement instance.

    Returns:
        Requirement: The updated  STW Requirement instance.
    """
        
        file_list = validated_data.pop('file_list', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        with transaction.atomic():
            instance.save()
            # Update associated documents if file_list is provided
            if file_list and len(file_list) > 0:
                for file in file_list:
                    try:
                        unique_filename = f"{str(uuid.uuid4())}_{file.name}"
                        upload_file_to_s3(unique_filename, file, f'work_planning/{instance.id}')
                        file_path = f'work_planning/{instance.id}/{unique_filename}'

                        STWAsset.objects.create(
                            stw_id=instance,
                            document_path=file_path,
                        )
                    except Exception as e:
                        print(f"Error uploading file {file.name}: {str(e)}")
        
        return instance
    
    def to_representation(self, instance):
        """
        Serialize the stw instance.

        Parameters:
            instance (Conversation): The stw instance.

        Returns:
            dict: The serialized representation of the stw.
        """
        representation = super().to_representation(instance)

        document_paths = []
        if hasattr(instance, 'stwasset_set'):
            for document in STWAsset.objects.filter(stw_id=instance):
                document_paths.append({
                    'presigned_url': generate_presigned_url(document.document_path),
                    'filename': document.document_path.split('/')[-1],
                    'id': document.id  #  document ID
                })

        representation['document_paths'] = document_paths

        return representation
    

class STWDefectSerializer(serializers.ModelSerializer):
    """
    Serializer for adding stw Requirement Defects with associated documents.

    This serializer handles the creation and updating of stw Requirement Defect instances along with associated documents.

    Args:
        serializers.ModelSerializer: Django REST framework model serializer.

    Attributes:
        action (serializers.CharField): Char field for the defect action.
        description (serializers.CharField): Char field for the defect description.
        rectification_description (serializers.CharField): Char field for the rectification description.
        file_list (serializers.ListField): List field for multiple files associated with the defect.
    """
    action = serializers.CharField(
        required=True, 
        style={'base_template': 'textarea.html'},
        error_messages={
            "required": "This field is required.",
            "blank": "Action is required.",
        },
        validators=[no_spaces_or_tabs_validator],
    )
    
    description = serializers.CharField(
        required=True, 
        style={'base_template': 'textarea.html'},
        error_messages={
            "required": "This field is required.",
            "blank": "Description is required.",
        },
        validators=[validate_description],
    )
    
    rectification_description = serializers.CharField(
        required=True, 
        style={'base_template': 'textarea.html'},
        error_messages={
            "required": "This field is required.",
            "blank": "Rectification description is required.",
        },
        validators=[validate_rectification_description],
    )
    
    file_list = serializers.ListField(
        child=serializers.FileField(
                allow_empty_file=False,
                validators=[CustomFileValidator()],
            ),
    label=('Documents'),  # Adjust the label as needed
    required=False,
    write_only=True,
    initial=[],
    style={
        "input_type": "file",
        "class": "form-control",
        "autofocus": False,
        "autocomplete": "off",
        'base_template': 'custom_multiple_file.html',
        'help_text': True,
        'multiple': True,
        'accept': ','.join(settings.IMAGE_VIDEO_SUPPORTED_EXTENSIONS),  # Set the accepted file extensions
        'allow_null': True,  # Allow None values
        'custom_class': 'col-6'
    },
    help_text=('Supported file extensions: ' + ', '.join(settings.IMAGE_VIDEO_SUPPORTED_EXTENSIONS))
    )
    
    defect_type = serializers.ChoiceField(
        label='Defect Type',
        choices=STW_DEFECT_CHOICES,
        default='actual_defect',  # Set the default choice here
        style={'base_template': 'radio.html', 'inline':True, 'custom_class': 'col-6'},)

    def get_initial(self):
        """
        Get the initial data for the serializer fields.

        Returns:
            OrderedDict: The initial data for the serializer fields.
        """
        
        fields = self.fields
        
        if hasattr(self, 'initial_data'):
            # initial_data may not be a valid type
            if not isinstance(self.initial_data, Mapping):
                return OrderedDict()

            if not self.instance:
                fields['file_list'].required = True

            return OrderedDict([
                (field_name, field.get_value(self.initial_data))
                for field_name, field in fields.items()
                if (field.get_value(self.initial_data) is not empty) and
                not field.read_only
            ])

        fields['file_list'].required = True
        
        return OrderedDict([
            (field.field_name, field.get_initial())
            for field in fields.values()
            if not field.read_only
        ])

        
    class Meta:
        model = STWDefect
        fields = ('action',  'description', 'rectification_description',  'defect_type','file_list')

    
    def create(self, validated_data):
        """
        Create a new STW  Defect instance with associated documents.

        Args:
            validated_data (dict): Validated data for creating a STW  Defect instance.

        Returns:
            STWDefect: The created STW Defect instance.
        """
        # Pop the 'file_list' field from validated_data
        file_list = validated_data.pop('file_list', None)
        
        # Create a new instance of STW Requirement with other fields from validated_data
        instance = STWDefect.objects.create(**validated_data)

        if file_list and len(file_list) > 0:

            for file in file_list:
                # Generate a unique filename for each file
                unique_filename = f"{str(uuid.uuid4())}_{file.name}"
                upload_file_to_s3(unique_filename, file, f'work_planning/{instance.id}/defects')
                file_path = f'work_planning/{instance.id}/defects/{unique_filename}'
                
                document = STWDefectDocument.objects.create(
                stw_id=instance.stw_id,
                defect_id = instance,
                document_path=file_path,
                )
            

class JobSerializer(serializers.ModelSerializer):

    UPRN = serializers.CharField(
        label=('UPRN'),
        required=True, 
        max_length=12,
        style={'base_template': 'custom_input.html'},
        error_messages={
            "required": "This field is required.",
            "blank": "UPRN is required.",
        },
    )

    RBNO = serializers.CharField(
        label=('RBNO'),
        required=True,
        max_length=12,
        style={'base_template': 'custom_input.html'},
        error_messages={
            "required": "This field is required.",
            "blank": "RBNO is required.",
        },
    )

    action = serializers.CharField(
        required=True, 
        style={'base_template': 'textarea.html'},
        error_messages={
            "required": "This field is required.",
            "blank": "Action is required.",
            "null": "Action is required."
        },
        validators=[action_description],
        
    )

    description = serializers.CharField(
        required=True, 
        style={'base_template': 'textarea.html'},
        error_messages={
            "required": "This field is required.",
            "blank": "Description is required.",
            "null": "Description is required."
        },
        validators=[validate_description],
        
    )
    date = serializers.DateField(
        required=True, 
        style={'base_template': 'custom_input.html'},
        error_messages={
            "required": "This field is required.",
            "blank": "Description is required.",
            "null": "Description is required."
        },
        validators=[validate_description],
    )
    Surveyor_name = serializers.CharField(
        required=True, 
        style={'base_template': 'custom_input.html'},
        error_messages={
            "required": "This field is required.",
            "blank": "Description is required.",
            "null": "Description is required."
        },
        validators=[validate_description],
     )
    No_of_defects = serializers.IntegerField(
        required=True, 
       style={'base_template': 'custom_input.html'},
        error_messages={
            "required": "This field is required.",
            "blank": "Description is required.",
            "null": "Description is required."
        },
        validators=[validate_description],
     )
    Defects_descreption = serializers.CharField(
        required=True, 
        style={'base_template': 'textarea.html'},
        error_messages={
            "required": "This field is required.",
            "blank": "Description is required.",
            "null": "Description is required."
        },
        validators=[validate_description],
     )
    class Meta:
        model = Job
        fields = ( 'UPRN', 'RBNO' ,'date','No_of_defects' , 'action','description','Defects_descreption' ,'Surveyor_name')

    def update(self, instance, validated_data):
        """
        Update an existing STW Defect instance with associated documents.

        Args:
            instance (STWDefect): The existing STW Defect instance to be updated.
            validated_data (dict): Validated data for updating the stw  Defect instance.

        Returns:
            RequirementDefect: The updated STW Defect instance.
        """
        file_list = validated_data.pop('file_list', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        with transaction.atomic():
            instance.save()

            # Update associated documents if file_list is provided
            if file_list and len(file_list) > 0:
                
                for file in file_list:
                    unique_filename = f"{str(uuid.uuid4())}_{file.name}"
                    upload_file_to_s3(unique_filename, file, f'work_planning/{instance.id}/defects')
                    file_path = f'work_planning/{instance.id}/defects/{unique_filename}'
                
                    STWDefectDocument.objects.create(
                        stw_id=instance.stw_id,
                        defect_id=instance,
                        document_path=file_path,
                    )
        
        return instance
    
    def to_representation(self, instance):
        """
        Serialize the stw Defect instance.

        Args:
            instance (STWDefect): The stw Defect instance.

        Returns:
            dict: The serialized representation of the stw Defect.
        """
        representation = super().to_representation(instance)

        document_paths = []
        if hasattr(instance, 'stwdefectdocument_set'):
            for document in STWDefectDocument.objects.filter(defect_id=instance, stw_id=instance.stw_id):
                document_paths.append({
                    'presigned_url': generate_presigned_url(document.document_path),
                    'filename': document.document_path.split('/')[-1],
                    'id': document.id  #  document ID
                })

        representation['document_paths'] = document_paths

        return representation
