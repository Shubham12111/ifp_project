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
    """
    Custom serializer field for displaying a customer's full name.

    This field is used to represent a customer's full name when serializing data.

    Methods:
        to_representation: Convert the customer object to its full name representation.
    """
    def to_representation(self, value):
        """
        Convert the customer object to its full name representation.

        Args:
            value (User): The customer object to represent.

        Returns:
            str: The full name of the customer.
        """
        return f"{value.first_name} {value.last_name}"

class CustomFileValidator(FileExtensionValidator):
    """
    Custom file validator for validating file extensions and size.

    This validator extends the functionality of Django's FileExtensionValidator by also checking
    the file size to ensure it doesn't exceed a maximum allowed size.

    Attributes:
        allowed_extensions (list): The list of allowed file extensions.
    """
    def __init__(self, allowed_extensions=settings.IMAGE_VIDEO_SUPPORTED_EXTENSIONS, *args, **kwargs):
        """
        Initialize the CustomFileValidator.

        Args:
            allowed_extensions (list): The list of allowed file extensions.
        """
        super().__init__(allowed_extensions, *args, **kwargs)

    def __call__(self, value):
        """
        Validate the file's extension and size.

        This method checks both the file extension and size to ensure they meet the specified criteria.

        Args:
            value (File): The uploaded file.

        Raises:
            serializers.ValidationError: If the file extension or size is invalid.
        """
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
    """
    Serializer for RequirementDefect model.

    This serializer is used to convert RequirementDefect model instances to JSON representations.

    Methods:
        to_representation: Convert the model instance to JSON representation.
    """
    
    class Meta:
        model = RequirementDefect
        fields = ('id', 'requirement_id', 'action', 'description', 'reference_number', 'rectification_description','defect_period', 'due_date', 'status')

    def to_representation(self, instance):
        """
        Convert the model instance to JSON representation.

        Args:
            instance (RequirementDefect): The RequirementDefect model instance.

        Returns:
            dict: JSON representation of the model instance.
        """
        data = super().to_representation(instance)
        data['description'] = strip_tags(data['description']) # to strip html tags attached to response by ckeditor RichText field.
        return data

class RequirementDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for Requirement model with additional details.

    This serializer is used to convert Requirement model instances to JSON representations with additional details.

    Fields:
        customer_name (CustomerNameField): A custom field for representing the customer's full name.
        quantity_surveyor_name (CustomerNameField): A custom field for representing the quantity surveyor's full name.
        requirementdefect_set (RequirementDefectSerializer): A nested serializer for RequirementDefect instances.

    Methods:
        to_representation: Convert the model instance to JSON representation.
    """
    customer_name = CustomerNameField(source='customer_id', read_only=True)
    quantity_surveyor_name = CustomerNameField(source='quantity_surveyor', read_only=True)
    requirementdefect_set = RequirementDefectSerializer(many=True, read_only=True)
    class Meta:
        model = Requirement
        fields = ('user_id', 'customer_id', 'description', 'RBNO', 'UPRN', 'quantity_surveyor', 'status', 'customer_name', 'quantity_surveyor_name', 'requirementdefect_set')

    def to_representation(self, instance):
        """
        Convert the model instance to JSON representation.

        Args:
            instance (Requirement): The Requirement model instance.

        Returns:
            dict: JSON representation of the model instance.
        """
        data = super().to_representation(instance)
        data['description'] = strip_tags(data['description']) # to strip html tags attached to response by ckeditor RichText field.
        return data


class CustomerSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'company_name')

class RequirementSerializer(serializers.ModelSerializer):
    """
    Serializer for Requirement model.

    This serializer is used to convert Requirement model instances to JSON representations.

    Methods:
        to_representation: Convert the model instance to JSON representation.
    """

    class Meta:
        model = Requirement
        fields = ('user_id', 'customer_id', 'description', 'quantity_surveyor', 'status')

    def to_representation(self, instance):
        """
        Convert the model instance to JSON representation.

        Args:
            instance (Requirement): The Requirement model instance.

        Returns:
            dict: JSON representation of the model instance.
        """
        data = super().to_representation(instance)
        data['description'] = strip_tags(data['description']) # to strip html tags attached to response by ckeditor RichText field.
        return data

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



class RequirementAddSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating Requirement instances with additional fields.

    This serializer includes additional fields such as 'action', 'RBNO', 'UPRN', 'description',
    'site_address', and 'file_list' to create and update Requirement instances.

    Fields:
        action (str): The action associated with the Requirement.
        RBNO (str): The RBNO (Reference Building Number) associated with the Requirement.
        UPRN (str): The UPRN (Unique Property Reference Number) associated with the Requirement.
        description (str): The description of the Requirement.
        site_address (SiteAddressField): A field for selecting the site address.
        file_list (List[FileField]): A list of files associated with the Requirement.

    Methods:
        validate_RBNO: Validate the uniqueness of RBNO.
        validate_UPRN: Validate the uniqueness of UPRN.
        get_initial: Get the initial data for the serializer.
        create: Create a new Requirement instance with associated files.
        update: Update an existing Requirement instance with associated files.
    """
    
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
        fields = ('RBNO', 'UPRN', 'action','description','site_address','file_list')
    
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
            if Requirement.objects.filter(RBNO=value).exists():
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
            if Requirement.objects.filter(UPRN=value).exists():
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
    Create a new Requirement instance with associated files.

    Args:
        validated_data (dict): Validated data for creating a Requirement instance.

    Returns:
        Requirement: The created Requirement instance.
    """
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
        """
    Update an existing Requirement instance with associated files.

    Args:
        instance (Requirement): The existing Requirement instance to be updated.
        validated_data (dict): Validated data for updating the Requirement instance.

    Returns:
        Requirement: The updated Requirement instance.
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
    """
    Serializer for adding Requirement Defects with associated documents.

    This serializer handles the creation and updating of Requirement Defect instances along with associated documents.

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
        choices=REQUIREMENT_DEFECT_CHOICES,
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
        model = RequirementDefect
        fields = ('action',  'description', 'rectification_description',  'defect_type','file_list')

    
    def create(self, validated_data):
        """
        Create a new Requirement Defect instance with associated documents.

        Args:
            validated_data (dict): Validated data for creating a Requirement Defect instance.

        Returns:
            RequirementDefect: The created Requirement Defect instance.
        """
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
        """
        Update an existing Requirement Defect instance with associated documents.

        Args:
            instance (RequirementDefect): The existing Requirement Defect instance to be updated.
            validated_data (dict): Validated data for updating the Requirement Defect instance.

        Returns:
            RequirementDefect: The updated Requirement Defect instance.
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
                    upload_file_to_s3(unique_filename, file, f'requirement/{instance.id}/defects')
                    file_path = f'requirement/{instance.id}/defects/{unique_filename}'
                
                    RequirementDefectDocument.objects.create(
                        requirement_id=instance.requirement_id,
                        defect_id=instance,
                        document_path=file_path,
                    )
        
        return instance
    
    def to_representation(self, instance):
        """
        Serialize the Requirement Defect instance.

        Args:
            instance (RequirementDefect): The Requirement Defect instance.

        Returns:
            dict: The serialized representation of the Requirement Defect.
        """
        representation = super().to_representation(instance)

        document_paths = []
        if hasattr(instance, 'requirementdefectdocument_set'):
            for document in RequirementDefectDocument.objects.filter(defect_id=instance, requirement_id=instance.requirement_id):
                document_paths.append({
                    'presigned_url': generate_presigned_url(document.document_path),
                    'filename': document.document_path.split('/')[-1],
                    'id': document.id  #  document ID
                })

        representation['document_paths'] = document_paths

        return representation






class RequirementAssetSerializer(serializers.Serializer):
    """
    Serializer for Requirement Asset information.

    This serializer is used to represent Requirement Asset information, including the associated Requirement,
    and provide URLs for accessing the associated documents.

    Attributes:
        requirement_id (serializers.PrimaryKeyRelatedField): Primary key related field to Requirement model.

    Methods:
        to_representation(instance: RequirementAsset): Serialize the Requirement Asset instance.

    Args:
        serializers.Serializer: Django REST framework serializer.

    """

    requirement_id = serializers.PrimaryKeyRelatedField(queryset=Requirement.objects.all())

    class Meta:
        model = RequirementAsset
        fields = ('__all__')

    def to_representation(self, instance: RequirementAsset):
        """
        Serialize the Requirement Asset instance.

        Args:
            instance (RequirementAsset): The Requirement Asset instance to be serialized.

        Returns:
            dict: The serialized representation of the Requirement Asset.
        """
        ret = super().to_representation(instance)

        ret['requirement_id'] = {'id': instance.requirement_id.id, 'name': instance.requirement_id.__str__()}

        ret['document_path'] = {'name': instance.document_path,  'url': generate_presigned_url(instance.document_path) }
        return ret

class RequirementDefectDocumentSerializer(serializers.Serializer):
    """
    Serializer for Requirement Defect Document information.

    This serializer is used to represent Requirement Defect Document information, including the associated Requirement,
    Defect, and provide URLs for accessing the associated documents.

    Attributes:
        requirement_id (serializers.PrimaryKeyRelatedField): Primary key related field to Requirement model.
        defect_id (serializers.PrimaryKeyRelatedField): Primary key related field to RequirementDefect model.

    Methods:
        to_representation(instance: RequirementDefectDocument): Serialize the Requirement Defect Document instance.

    Args:
        serializers.Serializer: Django REST framework serializer.

    """

    requirement_id = serializers.PrimaryKeyRelatedField(queryset=Requirement.objects.all())
    defect_id = serializers.PrimaryKeyRelatedField(queryset=RequirementDefect.objects.all())

    class Meta:
        model = RequirementDefectDocument
        fields = ('__all__')

    def to_representation(self, instance: RequirementDefectDocument):
        """
        Serialize the Requirement Defect Document instance.

        Args:
            instance (RequirementDefectDocument): The Requirement Defect Document instance to be serialized.

        Returns:
            dict: The serialized representation of the Requirement Defect Document.
        """
        ret = super().to_representation(instance)

        ret['requirement_id'] = {'id': instance.requirement_id.id, 'name': instance.requirement_id.__str__()}
        ret['defect_id'] = {'id': instance.defect_id.id, 'name': instance.defect_id.__str__()}

        ret['document_path'] = {'name': instance.document_path,  'url': generate_presigned_url(instance.document_path) }
        return ret


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
        required=True,
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
            'accept': ".png, .jpg, .jpeg",
            'allow_null': True,  # Allow None values
        },
        help_text=('Supported file extensions: ' + ', '.join(settings.IMAGE_SUPPORTED_EXTENSIONS))
        )
        
    class Meta:
        model = SORItem
        fields = ['name','reference_number','category_id','price', 'description','file_list']

        
    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Price cannot be negative.")
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
        Validate that the reference number (SKU) i unique.
        """
        if self.instance:
            reference_number = SORItem.objects.filter(reference_number=value).exclude(id=self.instance.id).exists()
        else:
            reference_number = SORItem.objects.filter(reference_number=value).exists()
        
        if reference_number:
            raise serializers.ValidationError("This SOR code is already in Use.")
        
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