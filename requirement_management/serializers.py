import uuid
from django.conf import settings
from rest_framework import serializers
from rest_framework.fields import empty
from .models import *
from django.utils.html import strip_tags
from authentication.models import User
from customer_management.models import SiteAddress
from infinity_fire_solutions.custom_form_validation import *
from infinity_fire_solutions.aws_helper import *
from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from collections import OrderedDict
from collections.abc import Mapping

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
        fields = ('id', 'requirement_id', 'action', 'description', 'reference_number', 'rectification_description','defect_period', 'due_date', 'status')

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
        fields = ('user_id', 'customer_id', 'description', 'UPRN', 'quantity_surveyor', 'status', 'customer_name', 'quantity_surveyor_name', 'requirementdefect_set')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['description'] = strip_tags(data['description']) # to strip html tags attached to response by ckeditor RichText field.
        return data

class RequirementCustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'company_name')

class RequirementSerializer(serializers.ModelSerializer):

    class Meta:
        model = Requirement
        fields = ('user_id', 'customer_id', 'description', 'quantity_surveyor', 'status')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['description'] = strip_tags(data['description']) # to strip html tags attached to response by ckeditor RichText field.
        return data

class SiteAddressField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        # Get the user_id from the request's query parameters
        user_id = self.context['request'].parser_context['kwargs']['customer_id']
        # Filter the queryset based on the user_id
        if user_id:
            return SiteAddress.objects.filter(user_id=user_id)
        else:
            return SiteAddress.objects.none()
        
class RequirementAddSerializer(serializers.ModelSerializer):
    
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
    
    site_address = SiteAddressField(
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
        model = Requirement
        fields = ('action','description','site_address','file_list')
    
   
            
    def get_initial(self):
        
        fields = self.fields
        
        if hasattr(self, 'initial_data'):
            # initial_data may not be a valid type
            if not isinstance(self.initial_data, Mapping):
                return OrderedDict()

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
        file_list = validated_data.pop('file_list', None)
        instance = Requirement.objects.create(**validated_data)

        if file_list and len(file_list) > 0:
            for file in file_list:
                unique_filename = f"{str(uuid.uuid4())}_{file.name}"
                try:
                    upload_file_to_s3(unique_filename, file, f'requirement/{instance.id}')
                    file_path = f'requirement/{instance.id}/{unique_filename}'
                    
                    document = RequirementAsset.objects.create(requirement_id=instance, document_path=file_path)
                
                except Exception as e:
                    # Handle the exception (e.g., log the error) and decide what to do next
                    pass

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
                    try:
                        unique_filename = f"{str(uuid.uuid4())}_{file.name}"
                        upload_file_to_s3(unique_filename, file, f'requirement/{instance.id}')
                        file_path = f'requirement/{instance.id}/{unique_filename}'

                        RequirementAsset.objects.create(
                            requirement_id=instance,
                            document_path=file_path,
                        )
                    except Exception as e:
                        print(f"Error uploading file {file.name}: {str(e)}")
        
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
    },
    help_text=('Supported file extensions: ' + ', '.join(settings.IMAGE_VIDEO_SUPPORTED_EXTENSIONS))
    )

   
    

    def get_initial(self):
        
        fields = self.fields
        
        if hasattr(self, 'initial_data'):
            # initial_data may not be a valid type
            if not isinstance(self.initial_data, Mapping):
                return OrderedDict()

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
        model = RequirementDefect
        fields = ('action',  'description', 'rectification_description', 'file_list')

    
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
                
                document = RequirementDefectDocument.objects.create(
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
                
                    RequirementDefectDocument.objects.create(
                        requirement_id=instance.requirement_id,
                        defect_id=instance,
                        document_path=file_path,
                    )
        
        return instance
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)

        document_paths = []
        if hasattr(instance, 'requirementdocument_set'):
            for document in RequirementDefectDocument.objects.filter(defect_id=instance, requirement_id=instance.requirement_id):
                document_paths.append({
                    'presigned_url': generate_presigned_url(document.document_path),
                    'filename': document.document_path.split('/')[-1],
                    'id': document.id  #  document ID
                })

        representation['document_paths'] = document_paths

        return representation






class RequirementAssetSerializer(serializers.Serializer):

    requirement_id = serializers.PrimaryKeyRelatedField(queryset=Requirement.objects.all())

    class Meta:
        model = RequirementAsset
        fields = ('__all__')

    def to_representation(self, instance: RequirementAsset):
        ret = super().to_representation(instance)

        ret['requirement_id'] = {'id': instance.requirement_id.id, 'name': instance.requirement_id.__str__()}

        ret['document_path'] = {'name': instance.document_path,  'url': generate_presigned_url(instance.document_path) }
        return ret

class RequirementDefectDocumentSerializer(serializers.Serializer):

    requirement_id = serializers.PrimaryKeyRelatedField(queryset=Requirement.objects.all())
    defect_id = serializers.PrimaryKeyRelatedField(queryset=RequirementDefect.objects.all())

    class Meta:
        model = RequirementDefectDocument
        fields = ('__all__')

    def to_representation(self, instance: RequirementDefectDocument):
        ret = super().to_representation(instance)

        ret['requirement_id'] = {'id': instance.requirement_id.id, 'name': instance.requirement_id.__str__()}
        ret['defect_id'] = {'id': instance.defect_id.id, 'name': instance.defect_id.__str__()}

        ret['document_path'] = {'name': instance.document_path,  'url': generate_presigned_url(instance.document_path) }
        return ret
