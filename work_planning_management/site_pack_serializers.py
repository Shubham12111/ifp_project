from rest_framework import serializers
from authentication.models import User
import re
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

from rest_framework import serializers
from rest_framework.fields import empty

from collections import OrderedDict
from collections.abc import Mapping

from infinity_fire_solutions.custom_form_validation import *
from infinity_fire_solutions.aws_helper import *

from .models import *



class CustomFileValidator(FileExtensionValidator):
    def __init__(self, allowed_extensions=settings.SUPPORTED_EXTENSIONS, *args, **kwargs):
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
        

class DocumentSerializer(serializers.ModelSerializer):
    """
    Serializer for adding a new Document.
    """
    name = serializers.CharField(
        label=('Name'),
        required=True,
        style={'base_template': 'custom_input.html'},
        error_messages={
            "required": "This field is required.",
            "blank": "Name is required.",
        },
    )
   
    file_list = serializers.ListField(
        child=serializers.FileField(
            allow_empty_file=False,
            validators=[CustomFileValidator()],
        ),
        label=('Upload File'),  # Adjust the label as needed
        required=True,
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
            'accept': '.png, .jpg, .jpeg, .doc, .docx, .pdf, .txt, .zip, .csv , .xls, .xlsx ',
            'allow_null': True,
            'custom_class':'col-6'
        },
        help_text=('Supported file extensions: ' + ', '.join(settings.SUPPORTED_EXTENSIONS))
    )
    
    
    class Meta:
        model = SitePack
        fields = ('name','file_list',)


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
    Create a new SitepackDocument  instance with associated files.

    Args:
        validated_data (dict): Validated data for creating a SitepackDocument instance.

    Returns:
        SitepackDocument: The created SitepackDocument instance.
    """
        file_list = validated_data.pop('file_list', None)
        instance = SitepackDocument.objects.create(**validated_data)
        print(instance)

        if file_list and len(file_list) > 0:
            for file in file_list:
                unique_filename = f"{str(uuid.uuid4())}_{file.name}"
                try:
                    upload_file_to_s3(unique_filename, file, f'sitepack_doc/{instance.id}')
                    file_path = f'sitepack_doc/{instance.id}/{unique_filename}'
                    
                    document = SitepackAsset.objects.create(sitepack_id=instance, document_path=file_path)
                
                except Exception as e:
                    # Handle the exception (e.g., log the error) and decide what to do next
                    pass

        return instance
    
 
    
    def to_representation(self, instance):
        """
        Serialize the SitepackDocument instance.

        Parameters:
            instance (Conversation): The SitepackDocument instance.

        Returns:
            dict: The serialized representation of the SitepackDocument.
        """
        representation = super().to_representation(instance)

        document_paths = []
        if hasattr(instance, 'sitepackasset_set'):
            for document in SitepackAsset.objects.filter(sitepack_id=instance):
                document_paths.append({
                    'presigned_url': generate_presigned_url(document.document_path),
                    'filename': document.document_path.split('/')[-1],
                    'id': document.id  #  document ID
                })

        representation['document_paths'] = document_paths

        return representation

 
class SitePackJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobDocument
        fields = ['job', 'sitepack_document']

class DocumentSelectSerializer(serializers.ModelSerializer):
    sitepack_document = serializers.PrimaryKeyRelatedField(
        label=('Select Document'),
        queryset = SitePack.objects.all(),
        style={'base_template': 'custom_select.html'},
        error_messages={
            "required": "This field is required.",
            "blank": "Name is required.",
        },
    )

    class Meta:
        model = JobDocument
        fields = ['sitepack_document']


# class DocumentViewSerializer(serializers.ModelSerializer):
#     """
#     Serializer for Document View.
#     """
#     presigned_url = serializers.SerializerMethodField()
#     filename = serializers.SerializerMethodField()

#     class Meta:
#         model = SitepackAsset
#         fields = ['sitepack_id', 'document_path', 'created_at', 'presigned_url', 'filename']

#     def get_presigned_url(self, document):
#         """
#         Get the pre-signed URL for the document.

#         Parameters:
#             document (document): The document instance.

#         Returns:
#             str: The pre-signed URL for the document or None if it doesn't exist.
#         """
#         # Check if 'document_path' exists and generate the pre-signed URL
#         if document.document_path:
#             presigned_url = generate_presigned_url(document.document_path)
#             return presigned_url
#         else:
#             return None

#     def get_filename(self, document):
#         """
#         Get the filename from the 'document_path'.

#         Parameters:
#             document (document): The document instance.

#         Returns:
#             str: The filename or None if it doesn't exist.
#         """
#         # Extract the filename from the 'document_path'
#         if document.document_path:
#             return document.document_path.split('/')[-1]
#         else:
#             return None
        





