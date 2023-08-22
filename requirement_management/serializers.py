import uuid
from django.conf import settings
from rest_framework import serializers
from .models import *
from django.utils.html import strip_tags
from authentication.models import User
from customer_management.models import SiteAddress
from infinity_fire_solutions.custom_form_validation import *
from infinity_fire_solutions.aws_helper import *
from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

class CustomerNameField(serializers.RelatedField):
    def to_representation(self, value):
        return f"{value.first_name} {value.last_name}"

class CustomFileValidator(FileExtensionValidator):
    def __init__(self, allowed_extensions=settings.IMAGE_VIDEO_SUPPORTED_EXTENSIONS, *args, **kwargs):
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

class RequirementDefectSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = RequirementDefect
        fields = ('id', 'requirement_id', 'action', 'description', 'defect_period', 'due_date', 'status')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['description'] = strip_tags(data['description']) # to strip html tags attached to response by ckeditor RichText field.
        return data
    

class RequirementDetailSerializer(serializers.ModelSerializer):
    customer_name = CustomerNameField(source='customer_id', read_only=True)
    quantity_surveyor_name = CustomerNameField(source='quantity_surveyor', read_only=True)
    requirementdefect_set = RequirementDefectSerializer(many=True, read_only=True)
    class Meta:
        model = Requirement
        fields = ('user_id', 'customer_id', 'description', 'UPRN', 'requirement_date_time', 'quantity_surveyor', 'status', 'customer_name', 'quantity_surveyor_name', 'requirementdefect_set')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['description'] = strip_tags(data['description']) # to strip html tags attached to response by ckeditor RichText field.
        return data

class RequirementSerializer(serializers.ModelSerializer):

    class Meta:
        model = Requirement
        fields = ('user_id', 'customer_id', 'description', 'requirement_date_time', 'quantity_surveyor', 'status')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['description'] = strip_tags(data['description']) # to strip html tags attached to response by ckeditor RichText field.
        return data

class RequirementAddSerializer(serializers.ModelSerializer):
    customer_id = serializers.PrimaryKeyRelatedField(
        label=('Customer'),
        required=True,
        queryset=User.objects.filter(roles__name='Customer'),
        style={
            'base_template': 'custom_customer_select.html',
            'custom_class':'col-12'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Customer is required.",
            "incorrect_type":"Customer is required.",
            "null": "Customer is required."
        },
    )
    description = serializers.CharField(
        max_length=1024, 
        required=True, 
        style={'base_template': 'rich_textarea.html'},
        error_messages={
            "required": "This field is required.",
            "blank": "Description is required.",
            "null": "Description is required."
        },
        validators=[validate_description],
        
    )
    
    requirement_date_time = serializers.DateTimeField(
        label='Date/Time',
        required=True,
        style={
            'base_template': 'custom_date_time.html',
            'custom_class': 'col-6'
        },
         error_messages={
            "required": "Date/Time is required.",
            "blank": "Date/Time is required.",
            "invalid": "Date/Time format. Use one of these formats instead: DD-MM-YYYY H:i",
            # You can add more error messages as needed
        }

    )
    
    reference_number = serializers.CharField(
        label=('Reference Number'),
        max_length=50,
        required = False,
        style={
            'base_template': 'custom_input.html',
            'custom_class':'col-6'
        },
        error_messages={
            "invalid": "Reference Number is invalid.",  
            "blank":"Reference Number is required.", 
        },
    )
   
    quantity_surveyor = serializers.PrimaryKeyRelatedField(
        label=('Quantity Surveyor'),
        required=True,
        queryset=User.objects.filter(roles__name = "quantity_surveyor"),
        style={
            'base_template': 'custom_select.html',
            'custom_class':'col-6'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Quantity Surveyor is required.",
            "incorrect_type":"Quantity Surveyor is required.",
            "null": "Quantity Surveyor is required."
        },
    )
    
    site_address = serializers.PrimaryKeyRelatedField(
        label=('Site Address'),
        required=True,
        queryset=SiteAddress.objects.all(),
        style={
            'base_template': 'custom_site_address_select.html',
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
        },
        help_text=('Supported file extensions: ' + ', '.join(settings.IMAGE_VIDEO_SUPPORTED_EXTENSIONS))
    )


    class Meta:
        model = Requirement
        fields = ('customer_id','description','site_address', 'quantity_surveyor', 'reference_number', 'requirement_date_time','file_list')
    
    def create(self, validated_data):
        # Pop the 'file_list' field from validated_data
        file_list = validated_data.pop('file_list', None)
        # Create a new instance of Requirement with other fields from validated_data
        instance = Requirement.objects.create(**validated_data)

        if file_list and len(file_list) > 0:

            for file in file_list:
                # Generate a unique filename for each file
                unique_filename = f"{str(uuid.uuid4())}_{file.name}"
                upload_file_to_s3(unique_filename, file, f'requirement/{instance.id}')
                file_path = f'requirement/{instance.id}/{unique_filename}'
                
                RequirementAsset.objects.create(
                requirement_id=instance,
                document_path=file_path,
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
                    print(file)
                    unique_filename = f"{str(uuid.uuid4())}_{file.name}"
                    upload_file_to_s3(unique_filename, file, f'requirement/{instance.id}')
                    file_path = f'requirement/{instance.id}/{unique_filename}'

                    RequirementAsset.objects.create(
                        requirement_id=instance,
                        document_path=file_path,
                    )
        
        return instance
    
    def to_representation(self, instance):
        """
        Serialize the Conversation instance.

        Parameters:
            instance (Conversation): The Conversation instance.

        Returns:
            dict: The serialized representation of the Conversation.
        """
        
        representation = super().to_representation(instance)

        document_paths = []
        if hasattr(instance, 'requirementasset_set'):
            for document in RequirementAsset.objects.filter(requirement_id=instance):
                document_paths.append({
                    'presigned_url': generate_presigned_url(document.document_path),
                    'filename': document.document_path.split('/')[-1],
                    'id': document.id  #  document ID
                })

        representation['document_paths'] = document_paths

        return representation
    
class RequirementDefectAddSerializer(serializers.ModelSerializer):
    action = serializers.CharField(
        max_length=500, 
        required=True, 
        style={'base_template': 'custom_fullwidth_input.html'},
        error_messages={
            "required": "This field is required.",
            "blank": "Action is required.",
        },
        validators=[no_spaces_or_tabs_validator],
    )
    
    description = serializers.CharField(
        max_length=1000, 
        required=True, 
        style={'base_template': 'rich_textarea.html'},
        error_messages={
            "required": "This field is required.",
            "blank": "Description is required.",
        },
        validators=[validate_description],
    )

    defect_period = serializers.DateTimeField(
        label='Defect Period',
        required=True,
        style={
            'base_template': 'custom_date_time.html',
            'custom_class': 'col-6'
        },
    )

    due_date = serializers.DateTimeField(
        label='Due Date',
        required=True,
        style={
            'base_template': 'custom_date_time.html',
            'custom_class': 'col-6'
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
        'accept': ','.join(settings.IMAGE_VIDEO_SUPPORTED_EXTENSIONS),  # Set the accepted file extensions
        'allow_null': True,  # Allow None values
    },
    help_text=('Supported file extensions: ' + ', '.join(settings.IMAGE_VIDEO_SUPPORTED_EXTENSIONS))
    )
    
    UPRN = serializers.CharField(
    max_length=12, 
    label=('UPRN'),
    required=False,  # Make it optional
    style={
        "autocomplete": "off",
        "required": False,  # Adjust as needed
        'base_template': 'custom_input.html',
        'custom_class': 'col-6'
    },
    error_messages={
            "blank": "UPRN Name is required.",
            "invalid": "It must contain a 12-digit number.",
        },
    )
    
    status = serializers.ChoiceField(
        label='Status',
        choices=REQUIREMENT_DEFECT_CHOICES,
        required=True,
        style={
            'base_template': 'custom_select.html',
            'custom_class': 'col-6'
        },
    )
    
    def validate_UPRN(self, value):
        cleaned_value = str(value).replace(" ", "")  # Remove spaces

        if not cleaned_value.isdigit() or len(cleaned_value) != 12:
            raise serializers.ValidationError("UPRN must be a 12-digit number.")

        if self.instance:
            queryset = RequirementDefect.objects.all().exclude(id=self.instance.id)
        else:
            queryset = RequirementDefect.objects.filter(UPRN=value)
        if queryset.filter(UPRN=cleaned_value).exists():
            raise serializers.ValidationError("A record with UPRN '{}' already exists.".format(cleaned_value))

        
        return value
    
    def validate(self, data):
        """
        Check that due_date is greater than defect_period.
        """
        defect_period = data.get('defect_period')
        due_date = data.get('due_date')

        if defect_period and due_date and defect_period >= due_date:
            raise serializers.ValidationError({"due_date": "Due date must be greater than defect period."})

        return data
        
    class Meta:
        model = RequirementDefect
        fields = ('action',  'description', 'defect_period', 'due_date', 'UPRN', 'status','file_list')
    
    def create(self, validated_data):
        # Pop the 'file_list' field from validated_data
        file_list = validated_data.pop('file_list', None)
        # Create a new instance of Requirement with other fields from validated_data
        instance = RequirementDefect.objects.create(**validated_data)

        if file_list and len(file_list) > 0:

            for file in file_list:
                # Generate a unique filename for each file
                unique_filename = f"{str(uuid.uuid4())}_{file.name}"
                upload_file_to_s3(unique_filename, file, f'requirement/{instance.id}/defects')
                file_path = f'requirement/{instance.id}/defects/{unique_filename}'
                
                document = RequirementDocument.objects.create(
                requirement_id=instance.requirement_id,
                defect_id = instance,
                document_path=file_path,
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
                    upload_file_to_s3(unique_filename, file, f'requirement/{instance.id}/defects')
                    file_path = f'requirement/{instance.id}/defects/{unique_filename}'
                
                    RequirementDocument.objects.create(
                        requirement_id=instance.requirement_id,
                        defect_id=instance,
                        document_path=file_path,
                    )
        
        return instance
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)

        document_paths = []
        if hasattr(instance, 'requirementdocument_set'):
            for document in RequirementDocument.objects.filter(defect_id=instance, requirement_id=instance.requirement_id):
                document_paths.append({
                    'presigned_url': generate_presigned_url(document.document_path),
                    'filename': document.document_path.split('/')[-1],
                    'id': document.id  #  document ID
                })

        representation['document_paths'] = document_paths

        return representation

class RequirementDefectResponseAddSerializer(serializers.ModelSerializer):
    
    rectification_description = serializers.CharField(
        max_length=1000, 
        required=True, 
        style={'base_template': 'rich_textarea.html'},
        error_messages={
            "required": "This field is required.",
            "blank": "Description is required.",
        },
        validators=[validate_description],
    )
    
    remedial_work = serializers.CharField(
        max_length=1000, 
        required=True, 
        style={'base_template': 'rich_textarea.html'},
        error_messages={
            "required": "This field is required.",
            "blank": "Remedial work is required.",
        },
        validators=[validate_description],
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
        "class": "form-control col-6",
        "autofocus": False,
        "autocomplete": "off",
        'base_template': 'custom_multiple_file.html',
        'help_text': True,
        'multiple': True,
        'accept': ','.join(settings.IMAGE_VIDEO_SUPPORTED_EXTENSIONS),  # Set the accepted file extensions
        'allow_null': True,  # Allow None values
    },
    help_text=('Supported file extensions: ' + ', '.join(settings.IMAGE_VIDEO_SUPPORTED_EXTENSIONS))
    )
    class Meta:
        model = RequirementDefectResponse
        fields = ('rectification_description', 'remedial_work', 'file_list')
        
        
    def create(self, validated_data):
    
        # Pop the 'file_list' field from validated_data
        file_list = validated_data.pop('file_list', None)
        
        instance = RequirementDefectResponse.objects.create(**validated_data)
        
        if file_list and len(file_list) > 0:

            for file in file_list:
                # Generate a unique filename for each file
                unique_filename = f"{str(uuid.uuid4())}_{file.name}"
                upload_file_to_s3(unique_filename, file, f'requirement/{instance.defect_id.requirement_id.id}/defects/{instance.defect_id.id}/responses')
                file_path = f'requirement/{instance.defect_id.requirement_id.id}/defects/{instance.defect_id.id}/responses/{unique_filename}'
                
                RequirementDefectResponseImage.objects.create(
                defect_response = instance,
                document_path=file_path,
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
                    upload_file_to_s3(unique_filename, file, f'requirement/{instance.defect_id.requirement_id.id}/defects/{instance.defect_id.id}/responses')
                    file_path = f'requirement/{instance.defect_id.requirement_id.id}/defects/{instance.defect_id.id}/responses/{unique_filename}'
                
                    RequirementDefectResponseImage.objects.create(
                        defect_response = instance,
                        document_path=file_path,
                    )
        
        return instance
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)

        document_paths = []
        if hasattr(instance, 'requirementdefectresponseimage_set'):
            for document in RequirementDefectResponseImage.objects.filter(defect_response=instance):
                document_paths.append({
                    'presigned_url': generate_presigned_url(document.document_path),
                    'filename': document.document_path.split('/')[-1],
                    'id': document.id  #  document ID
                })

        representation['document_paths'] = document_paths

        return representation