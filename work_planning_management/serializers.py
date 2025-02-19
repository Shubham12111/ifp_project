
from rest_framework import serializers
from requirement_management.models import Quotation  
from authentication.models import User
import re
import uuid
from datetime import datetime, timezone
from django.db import transaction

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags
from django.core.validators import FileExtensionValidator
from django.urls import reverse

from rest_framework import serializers
from rest_framework.fields import empty

from collections import OrderedDict
from collections.abc import Mapping

from authentication.models import User
from infinity_fire_solutions.custom_form_validation import *
from infinity_fire_solutions.aws_helper import *
from infinity_fire_solutions.validators import CustomImageFileValidator, CustomFileValidator
from customer_management.models import SiteAddress
from rest_framework.validators import UniqueValidator

from .models import *

from requirement_management.models import Requirement, RequirementDefect, RequirementDefectDocument, RequirementAsset


class QuotationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quotation
        fields = '__all__'
         
class CustomerSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'company_name')

class SiteAddressField(serializers.PrimaryKeyRelatedField):
    """
    Primary key related field for SiteAddress model.


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
    
    def display_value(self, instance):
        return f'{instance.address}, {instance.town}, {instance.country}, {instance.post_code}'

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
        max_length=1000, 
            required=True, 
            style={'base_template': 'rich_textarea.html', 'rows': 5},
            error_messages={
                "required": "This field is required.",
                "blank": "Message is required.",},
    )
    
    RBNO = serializers.CharField(
        label=('Job Number'),
        required=True,
        max_length=12,
        style={'base_template': 'custom_input.html'},
        error_messages={
            "required": "This field is required.",
            "blank": "Job Number is required.",
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
        max_length=1000, 
            required=True, 
            style={'base_template': 'rich_textarea.html', 'rows': 5},
            error_messages={
                "required": "This field is required.",
                "blank": "Message is required.",},
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

    building_name = serializers.CharField(
        label=('Building Name'),
        required=True, 
        style={'base_template': 'custom_input.html'},
        error_messages={
            "required": "This field is required.",
            "blank": "Building Name is required.",
            "null": "Building Name is required."
        },
        
    )

    postcode = serializers.CharField(
        label=('Post Code'),
        max_length=7,
        required=True,
        style={
            "input_type": "text",
            "autofocus": False,
            "autocomplete": "off",
            'base_template': 'custom_input.html',
            'placeholder': 'SW1A0NY'
        },
        validators=[validate_uk_postcode]
    )

    file_list = serializers.ListField(
        child=serializers.FileField(
            allow_empty_file=False,
            validators=[CustomImageFileValidator()],
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
        fields = ('RBNO','UPRN','action','description', 'site_address','building_name','postcode','file_list')
    
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
                raise serializers.ValidationError("Job Number already exists.")
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
    
    def validate_description(self, value):
        # Custom validation for the message field to treat <p><br></p> as blank
        soup = BeautifulSoup(value, 'html.parser')
        cleaned_comment = soup.get_text().strip()

        # Check if the cleaned comment consists only of whitespace characters
        if not cleaned_comment:
            raise serializers.ValidationError("Description is required.")

        if all(char.isspace() for char in cleaned_comment):
            raise serializers.ValidationError("Description cannot consist of only spaces and tabs.")

        return value
    
    def validate_action(self, value):
        # Custom validation for the message field to treat <p><br></p> as blank
        soup = BeautifulSoup(value, 'html.parser')
        cleaned_comment = soup.get_text().strip()

        # Check if the cleaned comment consists only of whitespace characters
        if not cleaned_comment:
            raise serializers.ValidationError("Action is required.")

        if all(char.isspace() for char in cleaned_comment):
            raise serializers.ValidationError("Action cannot consist of only spaces and tabs.")

        return value
    
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
    
class STWRequirementDetailsSerializer(serializers.ModelSerializer):

    class Meta:
        model = STWRequirements
        fields = ('RBNO','UPRN','action','description', 'site_address')
    
    def to_representation(self, instance):
        """
        Serialize the stw instance.

        Parameters:
            instance (Conversation): The stw instance.

        Returns:
            dict: The serialized representation of the stw.
        """
        representation = super().to_representation(instance)
        representation['file_list'] = [
            documents.id for documents in instance.stwasset_set.all()
        ] if instance.stwasset_set.all() else []
        return representation

class ConvertSTWToFRASerializer(serializers.ModelSerializer):
    action = serializers.CharField(
        required=True, 
        validators=[action_description],
        
    )
    RBNO = serializers.CharField(
        required=True,
        max_length=12,
        
    )
    UPRN = serializers.CharField(
        required=True, 
        max_length=12,
       
    )
    description = serializers.CharField(
        required=True, 
        
        validators=[validate_description],
        
    )
    site_address = serializers.PrimaryKeyRelatedField(
        required = True,
        queryset = SiteAddress.objects.all()
    )

    file_list = serializers.PrimaryKeyRelatedField(
        queryset = STWAsset.objects.all(),
        many=True
    )
    
    class Meta:
        model = Requirement
        fields = ('RBNO','UPRN','action','description', 'site_address', 'file_list')

    def create(self, validated_data):
        stw_documents = validated_data.pop('file_list', [])
        instance = super().create(validated_data)
        try:
            if stw_documents:
                for stw_document in stw_documents:
                    # Generate a unique filename for each file
                    unique_filename = f"{stw_document.document_path.split('/')[-1:][0]}"

                    file_path = f'requirement/{instance.id}/{unique_filename}'
                    move_s3_file(stw_document.document_path, file_path)
                    
                    document = RequirementAsset.objects.create(
                        requirement_id=instance,
                        document_path=file_path,
                    )
        except Exception as e:
            if 'NoSuchKey' not in str(e):
                instance.delete()
                raise serializers.ValidationError({
                    'file_list': str(e)
                })

        return instance

class ConvertSTWDefectsToFRADefectsSerializer(serializers.ModelSerializer):
    action = serializers.CharField(
        max_length=1000, 
        required=True, 
    )
    
    description = serializers.CharField(
        max_length=1000, 
        required=True, 
    )
    
    rectification_description = serializers.CharField(
        max_length=1000, 
        required=True, 
    )

    defect_type = serializers.ChoiceField(
        choices=STW_DEFECT_CHOICES,
        default='actual_defect',
    )

    file_list = serializers.PrimaryKeyRelatedField(
        queryset = STWDefectDocument.objects.all(),
        many=True
    )
    
    class Meta:
        model = RequirementDefect
        fields = ('action', 'description', 'rectification_description', 'defect_type', 'reference_number', 'file_list')
    
    def create(self, validated_data):
        stw_defect_documents = validated_data.pop('file_list', [])
        instance = super().create(validated_data)
        try:
            if stw_defect_documents:
                for stw_defect_document in stw_defect_documents:
                    # Generate a unique filename for each file
                    unique_filename = f"{stw_defect_document.document_path.split('/')[-1:][0]}"

                    file_path = f'requirement/{instance.id}/defects/{unique_filename}'
                    if stw_defect_document.document_path != 'work_planning/31/defects/6551be21-14f1-496f-a6b5-722e54ed684b_Screenshot from 2024-01-30 11-40-01.png':
                        move_s3_file(stw_defect_document.document_path, file_path)
                    
                    document = RequirementDefectDocument.objects.create(
                        requirement_id=instance.requirement_id,
                        defect_id = instance,
                        document_path=file_path,
                    )
        except Exception as e:
            if 'NoSuchKey' not in str(e):
                instance.delete()
                raise serializers.ValidationError({
                    'file_list': str(e)
                })

        return instance


class STWDefectsDetailedSerializer(serializers.ModelSerializer):
    class Meta:
        model = STWDefect
        fields = '__all__'
    
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['file_list'] = [
            documents.id for documents in instance.stwdefectdocument_set.all()
        ] if instance.stwdefectdocument_set.all() else []
        return ret
    

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
      # Custom CharField for the message with more rows (e.g., 5 rows)
    action = serializers.CharField(
            max_length=1000, 
            required=True, 
            style={'base_template': 'rich_textarea.html', 'rows': 5},
            error_messages={
                "required": "This field is required.",
                "blank": "Message is required.",},
    )
    
    description = serializers.CharField(
            max_length=1000, 
            required=True, 
            style={'base_template': 'rich_textarea.html', 'rows': 5},
            error_messages={
                "required": "This field is required.",
                "blank": "Message is required.",},
    )
    
    rectification_description = serializers.CharField(
            max_length=1000, 
            required=True, 
            style={'base_template': 'rich_textarea.html', 'rows': 5},
            error_messages={
                "required": "This field is required.",
                "blank": "Message is required.",},
    )

    
    file_list = serializers.ListField(
        child=serializers.FileField(
                allow_empty_file=False,
                validators=[CustomImageFileValidator()],
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

    def validate_description(self, value):
        # Custom validation for the message field to treat <p><br></p> as blank
        soup = BeautifulSoup(value, 'html.parser')
        cleaned_comment = soup.get_text().strip()

        # Check if the cleaned comment consists only of whitespace characters
        if not cleaned_comment:
            raise serializers.ValidationError("Description is required.")

        if all(char.isspace() for char in cleaned_comment):
            raise serializers.ValidationError("Description cannot consist of only spaces and tabs.")

        return value
    
    def validate_action(self, value):
        # Custom validation for the message field to treat <p><br></p> as blank
        soup = BeautifulSoup(value, 'html.parser')
        cleaned_comment = soup.get_text().strip()

        # Check if the cleaned comment consists only of whitespace characters
        if not cleaned_comment:
            raise serializers.ValidationError("Action is required.")

        if all(char.isspace() for char in cleaned_comment):
            raise serializers.ValidationError("Action cannot consist of only spaces and tabs.")

        return value
    
    def validate_rectification_description(self, value):
        # Custom validation for the message field to treat <p><br></p> as blank
        soup = BeautifulSoup(value, 'html.parser')
        cleaned_comment = soup.get_text().strip()

        # Check if the cleaned comment consists only of whitespace characters
        if not cleaned_comment:
            raise serializers.ValidationError("Rectification Description is required.")

        if all(char.isspace() for char in cleaned_comment):
            raise serializers.ValidationError("Rectification Description cannot consist of only spaces and tabs.")

        return value

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
            instance.save()
            return instance  # Return the created STWDefect instance
            

class JobListSerializer(serializers.ModelSerializer):
    UPRN = serializers.SerializerMethodField()
    RBNO = serializers.SerializerMethodField()
    Action = serializers.SerializerMethodField()
    Description = serializers.SerializerMethodField()
    Date = serializers.SerializerMethodField()
    Surveyor_Name = serializers.SerializerMethodField()
    Number_of_Defects = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = ['UPRN', 'RBNO', 'Action', 'Description', 'Date', 'Surveyor_Name', 'Number_of_Defects']

    def get_UPRN(self, obj):
        return obj.quotation.requirement_id.UPRN

    def get_RBNO(self, obj):
        return obj.quotation.requirement_id.RBNO

    def get_Action(self, obj):
        return obj.quotation.requirement_id.action

    def get_Description(self, obj):
        return obj.quotation.requirement_id.description

    def get_Date(self, obj):
        return obj.quotation.requirement_id.date

    def get_Surveyor_Name(self, obj):
        return f"{obj.quotation.requirement_id.surveyor.first_name} {obj.quotation.requirement_id.surveyor.last_name}"

    def get_Number_of_Defects(self, obj):
        return obj.quotation.defect_id.count()
    


class MemberSerializer(serializers.ModelSerializer):

    name = serializers.CharField(
        label=('Name'),
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


    address = serializers.CharField(
        label=('Address'),
        max_length=255,
        min_length=5,
        required=True,
        allow_blank=True,
        allow_null=True,
        style={'base_template': 'textarea.html'}  
    )

    trade_type = serializers.CharField(
        label='Trade/Type',
        required=True,
        error_messages={
            "required": "This field is required.",
            "blank": "Trade/Type is required.",
        },
        style={
            'base_template': 'custom_input.html'
        },
    )

    mobile_number = serializers.CharField(
        label=('Phone Number'),
        max_length=14,
        min_length=10,
        required=True,
        allow_null=True,
        allow_blank=True,
        style={
            'base_template': 'custom_input.html'
        },
        validators=[validate_phone_number] 
    )

    email = serializers.EmailField(
        label=('Email'),
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
    job_title = serializers.CharField(
        label='Job Title',
        required=True,
        error_messages={
            "required": "This field is required.",
            "blank": "Job Title is required.",
        },
          style={
            'base_template': 'custom_input.html'
        },
    )

    class Meta:
        model = Member 
        fields = ('name', 'email','mobile_number', 'trade_type','address', 'job_title' )

class TeamSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(
        label='Team Name',
        required=True,
        max_length=100,
        style={
            "input_type": "text",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
            'base_template': 'custom_input.html',   

        },
        error_messages={
            "required": "This field is required.",
            "blank": "Team Name is required.",
        }
    )
    
    class Meta:
        model = Team
        fields = ["team_name"]  # You can specify the fields you want explicitly if needed

class AddJobSerializer(serializers.ModelSerializer):
    """
    Serializer for adding a add JOb.

    Fields:
    - action: The JOb action description.
    - RBNO: The RBNO (Reference Base Number) for the Job.
    - UPRN: The UPRN (Unique Property Reference Number) for the Job.
    - description: The JOb description.
    - Date: The date of job created.

    Validators:
    - RBNO uniqueness validator.
    - UPRN uniqueness validator.
    """
    UPRN = serializers.SerializerMethodField()
    RBNO = serializers.SerializerMethodField()
    Action = serializers.SerializerMethodField()
    Description = serializers.SerializerMethodField()
    Site_address = serializers.SerializerMethodField()
    Date = serializers.SerializerMethodField()
    
    class Meta:
        model = Job
        fields = ['UPRN', 'RBNO', 'Action', 'Description', 'Date','Site_address']

    def get_UPRN(self, obj):
        return obj.stw.UPRN

    def get_RBNO(self, obj):
        return obj.stw.stw_id.RBNO

    def get_Action(self, obj):
        return obj.stw.stw_id.action

    def get_Description(self, obj):
        return obj.stw.stw_id.description
    
    def get_Site_Address(self, obj):
        return obj.stw.stw_id.site_address

    def get_Date(self, obj):
        return obj.stw.stw_id.date

   
class JobAssignmentSerializer(serializers.ModelSerializer):
    start_date = serializers.DateTimeField(
        label='Start Date',
        required=True,
        input_formats=['%d-%m-%Y %H:%M','iso-8601'],
        style={
            'base_template': 'custom_date_time.html',
            'custom_class': 'col-12 col-md-6'
        },
        # Add any additional styles or validators if needed
    )

    end_date = serializers.DateTimeField(
        label='End Date',
        required=True,
        input_formats=['%d-%m-%Y %H:%M','iso-8601'],
        style={
            'base_template': 'custom_date_time.html',
            'custom_class': 'col-12 col-md-6'
        },
        # Add any additional styles or validators if needed
    )

    quotation = serializers.PrimaryKeyRelatedField(
        queryset = Quotation.objects.filter(status='to-commence').all(),
        many=True,
        style={
            'base_template': 'custom_hidden_select_input.html',
            'custom_class': 'd-none'
        },
        required=False
    )

    stw = serializers.PrimaryKeyRelatedField(
        queryset = STWRequirements.objects.all(),
        many=True,
        style={
            'base_template': 'custom_hidden_select_input.html',
            'custom_class': 'd-none'
        },
        required=False
    )

    class Meta:
        model = Job
        fields = ['quotation', 'stw', 'start_date', 'end_date']
    
    def validate(self, attrs):
        customer = self.context.get('customer')
        attrs = super().validate(attrs)

        # get the quotations list
        quotations = attrs.get('quotation', [])
        quotations = [quotation for quotation in quotations if quotation.customer_id == customer]
        quotations = [quotation for quotation in quotations if not quotation.job_set.all()]
        
        stws = attrs.get('stw', [])
        stws = [stw for stw in stws if stw.customer_id == customer]
        stws = [stw for stw in stws if not stw.job_set.all()]

        if not stws and not quotations:
            raise serializers.ValidationError({
                'quotation': ['This field is required.'],
                'stw': ['This field is required.']
            })
         # Additional validation to check if all jobs have the same site_address
        site_address = set()
        for quotation in quotations:
            site_address.add(quotation.requirement_id.site_address)

        for stw in stws:
            site_address.add(stw.site_address)

        if len(site_address) > 1:
            raise serializers.ValidationError("You are not authorised to perform this operation")
        return attrs

class JobCreateSerializer(serializers.ModelSerializer):
    
    start_date = serializers.DateTimeField(
        label='Start Date',
        required=True,
        input_formats=['%d-%m-%Y %H:%M','iso-8601'],
        # Add any additional styles or validators if needed
    )

    end_date = serializers.DateTimeField(
        label='End Date',
        required=True,
        input_formats=['%d-%m-%Y %H:%M','iso-8601'],
        # Add any additional styles or validators if needed
    )

    quotation = serializers.PrimaryKeyRelatedField(
        queryset = Quotation.objects.filter(status='to-commence').all(),
        many=True,
        required=False
    )

    stw = serializers.PrimaryKeyRelatedField(
        queryset = STWRequirements.objects.all(),
        many=True,
        required=False
    )

    assigned_to_member = serializers.PrimaryKeyRelatedField(
        queryset = Member.objects.all(),
        many=True,
        required=False
    )

    assigned_to_team = serializers.PrimaryKeyRelatedField(
        queryset = Team.objects.all(),
        required=False
    )

    class Meta:
        model = Job
        fields = ['quotation', 'stw', 'start_date', 'end_date', 'assigned_to_team', 'assigned_to_member']
    
    def validate(self, attrs):
        data = super().validate(attrs)
        start_date = data.get('start_date', None)
        end_date = data.get('end_date', None)

        if start_date and end_date and start_date > end_date:
            raise ValidationError({'end_date':'End Date/Time should be greater than the Start Date/Time.'})
        
        if start_date == end_date:
            raise ValidationError({'end_date':'End Date/Time should be greater than the Start Date/Time.'})
        
        team = data.get('assigned_to_team', None)
        members = data.get('assigned_to_member', None)

        if not team and not members:
            raise ValidationError(
                {
                    'assigned_to_team':[
                        'Either team or member must be selected.'
                    ], 
                    'assigned_to_member': [
                        'Either team or member must be selected.'
                    ]
                }
            )

        errors = []
        members_list = []

        if team:
            members_list = [member for member in team.members.all()]
        
        if members:
            members_list.extend([member for member in members])
        
        if members_list:
            for member in members_list:
                teams = member.team_set.all()
                member_jobs = [job for team in teams for job in team.job_set.all()]
                member_jobs.extend(
                    [job for job in member.job_set.all().exclude(
                            id__in=[job.id for job in member_jobs]
                        )
                    ]
                )

                for job in member_jobs:
                    if start_date <= job.start_date <= end_date \
                        or job.start_date <= start_date <= job.end_date:
                        errors.append(f"A Member {'from this team' if team else ''} is already assigned to a job in the specified range.")
        
        if errors:
            errors = list(set(errors))
            raise ValidationError(
                    {
                        'start_date':errors, 
                        'end_date': errors
                    }
                )

        customer = self.context.get('customer')

        # get the quotations list
        quotations = data.get('quotation', [])
        quotations = [quotation for quotation in quotations if quotation.customer_id == customer]
        quotations = [quotation for quotation in quotations if not quotation.job_set.all()]
        
        stws = data.get('stw', [])
        stws = [stw for stw in stws if stw.customer_id == customer]
        stws = [stw for stw in stws if not stw.job_set.all()]

        data['stw'] = stws
        data['quotation'] = quotations

        return data

class AttachSitePackSerializer(serializers.ModelSerializer):

    job = serializers.PrimaryKeyRelatedField(
        queryset=Job.objects.all(),
        required=True,
        error_messages={
            "required": "This field is required.",
            "blank": "job is required.",
        },
    )

    sitepack_document = serializers.PrimaryKeyRelatedField(
        queryset=SitePack.objects.all(),
        required=True,
        error_messages={
            "required": "This field is required.",
            "blank": "Site Pack is required.",
        },
    )

    class Meta:
        model = JobDocument
        fields = ['job', 'sitepack_document']
    
    def validate(self, attrs):
        job = attrs.get('job', None)
        site_pack = attrs.get('sitepack_document', None)

        if not site_pack and not job:
            raise serializers.ValidationError(
                {
                    'job': ['This field is required.'],
                    'sitepack_document': ['This field is required.']
                }
            )

        queryset = self.Meta.model.objects.filter(job=job).values_list('sitepack_document', flat=True).all()

        if site_pack.id in queryset:
            raise serializers.ValidationError(
                {
                    'sitepack_document': ['The site pack is already attached to this job, please choose some another site pack.']
                }
            )

        return super().validate(attrs)

class AddAndAttachSitePackSerializer(serializers.ModelSerializer):

    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=True,
        error_messages={
            "required": "This field is required.",
            "blank": "Name is required.",
        },
    )

    job = serializers.PrimaryKeyRelatedField(
        queryset=Job.objects.all(),
        required=True,
        error_messages={
            "required": "This field is required.",
            "blank": "Name is required.",
        },
    )

    name = serializers.CharField(
        required=True,
        max_length=50,
        error_messages={
            "required": "This field is required.",
            "blank": "Name is required.",
        },
    )

    document_path = serializers.FileField(
        allow_empty_file=False,
        validators=[CustomFileValidator()],
        required=True,
        error_messages={
            'invalid': f'The file is not supported, supported file formats are: {", ".join(settings.SUPPORTED_EXTENSIONS)}',
            'max_size': f'The file size exceed from 5 MBs. Please ensure the file smaller than this.'
        }
    )

    class Meta:
        model = SitePack
        fields = ['user_id', 'job', 'name', 'document_path']
    
    def create(self, validated_data):

        document = validated_data.pop('document_path', None)
        job = validated_data.pop('job', None)
        try:
            orignal_document_name = f'{document.name}'
            document.name = f"{str(uuid.uuid4())}_{document.name}"
            # upload the document to the s3
            upload_file_to_s3(document.name, document, f'sitepack_doc')
            validated_data['document_path'] = f'{document.name}'
            validated_data['orignal_document_name'] = orignal_document_name
            instance = super().create(validated_data)
            serializer = AttachSitePackSerializer(data={
                'job': job.id,
                'sitepack_document': instance.id
            })

            if serializer.is_valid():
                serializer.save()
                return instance
            
            raise serializer.errors
        except Exception as e:
            raise e

    def delete(self, instance):
        site_pack = instance.sitepack_document

        if site_pack.user_id.is_staff:
            instance.delete()
        
        else:
            instance.delete()
            deleted = delete_file_from_s3(site_pack.document_path, f'sitepack_doc')
            site_pack.delete()


class CreateRLOSeirlaizer(serializers.ModelSerializer):

    name = serializers.CharField(
        required=True,
        max_length=255,
        error_messages={
            "required": "This field is required.",
            "blank": "Name is required.",
            "invalid": "Invalid Name",
        }, 
    )

    job = serializers.PrimaryKeyRelatedField(
        queryset=Job.objects.all(),
        required=True,
        error_messages={
            "required": "This field is required.",
            "blank": "job is required.",
        },
    )

    base_template = serializers.PrimaryKeyRelatedField(
        queryset=RLOLetterTemplate.objects.all(),
        required=True,
        error_messages={
            "required": "This field is required.",
            "blank": "Base Template is required.",
        },
    )

    class Meta:
        model = RLO
        fields = ('name', 'job', 'base_template', 'edited_content')
    
    def validate(self, attr):

        edited_content = attr.get('edited_content', None)
        base_template = attr.get('base_template', None)

        if not base_template:
            raise serializers.ValidationError(
                {
                    'base_template': ['This field is required.']
                }
            )

        if edited_content is not None:
            edited_content = edited_content
        else:
            edited_content = base_template.complete_template
        
        attr['edited_content'] = edited_content

        return super().validate(attr)

class UpdateRLOSeirlaizer(serializers.ModelSerializer):

    class Meta:
        model = RLO
        fields = ('status',)

class EventSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        label=('Name'),
        required=True,
        max_length=400,
        style={
            "input_type": "text",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
            'base_template': 'custom_input.html',
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Name is required.",
            "invalid": "Invalid Name",
        }, 
    )
    team = serializers.PrimaryKeyRelatedField(
        label=('Team'),
        required=False,
        allow_null=True,
        # allow_blank=True,
        queryset=Team.objects.all(),
        style={
            'base_template': 'custom_select.html',
             'custom_class':'col-6'
        },
    )
    member = serializers.MultipleChoiceField(
        label=('Member'),
        required=False,
        allow_null=True,
        allow_blank=True,
        choices=[member for member in Member.objects.all()]
        # choices = []
    )


    start = serializers.DateTimeField(
        label='Start Date',
        required=True,
        input_formats=['iso-8601'],
        style={
            'base_template': 'custom_datepicker.html',
            'custom_class': 'col-6'
        },
        # Add any additional styles or validators if needed
    )
    end = serializers.DateTimeField(
        label='End Date',
        required=True,
        input_formats=['iso-8601'],
        style={
            'base_template': 'custom_datepicker.html',
            'custom_class': 'col-6'
        },
       
    )

    description  = serializers.CharField(
        max_length=1000, 
        required=False, 
        style={'base_template': 'rich_textarea.html', 'rows': 3},
        error_messages={
            "required": "Description is required.",
            "blank":"Description is required.",
        },
        validators=[validate_description]
    )
    class Meta:
        model = Events
        fields = ['name', 'team','description','member','start', 'end'] 

class STWJobListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = [
            'id',
            'quotation',
            'stw',
            'assigned_to_member',
            'assigned_to_team',
            'event',
            'start_date',
            'end_date',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    # If you want to provide custom representation for related fields, you can do so like this:
    quotation = QuotationSerializer()
    stw = STWRequirementSerializer()
    assigned_to_member = MemberSerializer(many=True)
    assigned_to_team = TeamSerializer()
    event = EventSerializer()

class JobStatusUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating the status of a Job.
    """
    class Meta:
        model = Job
        fields = (
            'status',
        )


class MemberCalendarSerializer(serializers.ModelSerializer):
    """
    Serializer for Requirement model.

    This serializer is used to get Requirements for a Surveyor and convert Requirement model instances to JSON representations.

    Methods:
        to_representation: Convert the model instance to JSON representation.
    """

    class Meta:
        model = Member
        fields = ('name', )

    def to_representation(self, instance: Member):
        try:
            ret = []
            for ins in instance:
                className = 'bg-gradient-warning'
                teams = ins.team_set.all()
                jobs = [job for team in teams for job in team.job_set.all()]
                jobs.extend([job for job in ins.job_set.all().exclude(id__in=[job.id for job in jobs])])
                

                for job in jobs:
                    if job.status == 'completed':
                        className = 'bg-gradient-success'

                    title = job.__str__()
                    member = ins.name
                    start = job.start_date.strftime('%Y-%m-%dT%H:%M:%S')
                    end = job.end_date.strftime('%Y-%m-%dT%H:%M:%S')

                    if job.status != 'completed' and job.end_date < datetime.now(timezone.utc):
                        className = 'bg-gradient-danger'
                    ret.append(
                        {
                            'id': job.id,
                            'title': f'{member} - {ins.email}',
                            'description': f'{title}',
                            'start': f'{start}',
                            'end': f'{end}',
                            'className': f'{className}',
                            'url': f"{reverse('job_detail', kwargs={'customer_id': job.customer_id.id, 'job_id': job.id})}"
                        }
                    )
            return {'jobs': ret}
        except Exception as e:
            return {}

class TeamUpdateSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(
        label='Team Name',
        required=True,
        max_length=100,
        style={
            "input_type": "text",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
            'base_template': 'custom_input.html',   

        },
        error_messages={
            "required": "This field is required.",
            "blank": "Team Name is required.",
        }
    )

    selected_members = serializers.PrimaryKeyRelatedField(
        queryset=Member.objects.all(),
        many=True,
    )
    
    class Meta:
        model = Team
        fields = ["team_name", "selected_members"]  # You can specify the fields you want explicitly if needed
    
    def validate_selected_members(self, values):
        if not values:
            raise serializers.ValidationError('Pleae select members to add to this team.')

        if 6 < len(values) < 2:
            raise serializers.ValidationError('A team must have between 2 and 6 members.')
        return values
    
    def create(self, validated_data):
        members = validated_data.pop('selected_members', [])
        instance = super().create(validated_data)
        instance.members.set(members)
        return instance

    def update(self, instance, validated_data):
        members = validated_data.pop('selected_members', [])
        instance = super().update(instance, validated_data)
        instance.members.set(members)
        return instance

class STWRequirementsListSerializer(serializers.ModelSerializer):

    class Meta:
        model = STWRequirements
        fields = '__all__'

    def to_representation(self, instance):
        """
        Convert the model instance to JSON representation.

        Args:
            instance (Requirement): The Requirement model instance.

        Returns:
            dict: JSON representation of the model instance.
        """
        data = super().to_representation(instance)
        data['action'] = strip_tags(data['action']) # to strip html tags attached to response by ckeditor RichText field.
        data['description'] = strip_tags(data['description']) # to strip html tags attached to response by ckeditor RichText field.
        data['site_address'] = instance.site_address.site_name if instance.site_address else ''
        data['status'] = instance.get_status_display() if instance.status else ''
        data['created_at'] = f"{instance.created_at.strftime('%d/%m/%Y')}" if instance.created_at else ''
        data['updated_at'] = f"{instance.updated_at.strftime('%d/%m/%Y')}" if instance.updated_at else ''
        return data

class STWRequirementDefectSerializer(serializers.ModelSerializer):
    """
    Serializer for RequirementDefect model.

    This serializer is used to convert RequirementDefect model instances to JSON representations.

    Methods:
        to_representation: Convert the model instance to JSON representation.
    """
    
    class Meta:
        model = STWDefect
        fields = '__all__'

    def to_representation(self, instance):
        """
        Convert the model instance to JSON representation.

        Args:
            instance (RequirementDefect): The RequirementDefect model instance.

        Returns:
            dict: JSON representation of the model instance.
        """
        data = super().to_representation(instance)
        data['defect_type'] = instance.get_defect_type_display() if instance.defect_type else ''
        data['description'] = strip_tags(data['description']) # to strip html tags attached to response by ckeditor RichText field.
        data['action'] = strip_tags(data['action']) # to strip html tags attached to response by ckeditor RichText field.
        data['rectification_description'] = strip_tags(data['rectification_description']) # to strip html tags attached to response by ckeditor RichText field.
        return data