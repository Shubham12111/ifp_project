import re
import uuid
from .models import *
from django.db import transaction
from rest_framework import serializers
from infinity_fire_solutions.custom_form_validation import *
from infinity_fire_solutions.aws_helper import *
from django.conf import settings

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

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

class ItemSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(
        label=('Name'),
        max_length=500, 
        required=True, 
        style={
            'base_template': 'custom_input.html',
            'custom_class':'col-12'
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
        queryset=Category.objects.all(),
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
        },
    )
    
    reference_number = serializers.CharField(
        label=('Reference Number'),
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
    
    quantity_per_box = serializers.CharField(
        label=('Quantity Per Box'),
        max_length=50,
        required=False,
        style={
            'base_template': 'custom_input.html',
            'custom_class':'col-6 quantity_per_box'
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
        model = Item
        fields = ['item_name','category_id','price', 'description', 'units', 'quantity_per_box','reference_number','file_list']

        
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
        Validate that the reference number (SKU) is unique.
        """
        if self.instance:
            reference_number = Item.objects.filter(reference_number=value).exclude(id=self.instance.id).exists()
        else:
            reference_number = Item.objects.filter(reference_number=value).exists()
        
        if reference_number:
            raise serializers.ValidationError("This reference number is already in use.")
        
        return value

    
    def create(self, validated_data):
        # Pop the 'file_list' field from validated_data
        file_list = validated_data.pop('file_list', None)
        # Create a new instance of Requirement with other fields from validated_data
        instance = Item.objects.create(**validated_data)

        if file_list and len(file_list) > 0:

            for file in file_list:
                # Generate a unique filename for each file
                unique_filename = f"{str(uuid.uuid4())}_{file.name}"
                upload_file_to_s3(unique_filename, file, f'stock/item/{instance.id}')
                file_path = f'stock/item/{instance.id}/{unique_filename}'
                # save the Product images
                document = ItemImage.objects.create(
                item_id = instance,
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
                    upload_file_to_s3(unique_filename, file, f'stock/item/{instance.id}')
                    file_path = f'stock/item/{instance.id}/{unique_filename}'
                
                    ItemImage.objects.create(
                        item_id=instance,
                        image_path=file_path,
                )
        
        return instance
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)

        document_paths = []
        if hasattr(instance, 'itemimage_set'):  # Using 'itemimage_set' for images

            for document in ItemImage.objects.filter(item_id=instance):
                document_paths.append({
                    'presigned_url': generate_presigned_url(document.image_path),
                    'filename': document.image_path.split('/')[-1],
                    'id': document.id  #  document ID
                })

        
        representation['document_paths'] = document_paths
        return representation