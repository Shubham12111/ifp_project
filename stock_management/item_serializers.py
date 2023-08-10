import re
from .models import *
from rest_framework import serializers
import uuid
from django.conf import settings

class ItemSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(
        label=('Item Name'),
        max_length=500, 
        required=True, 
        style={
            'base_template': 'custom_input.html',
            'custom_class':'col-12'
        },
        error_messages={
            "required": "Item Name is required.",
        },
    )
    description = serializers.CharField(
        max_length=1000, 
        required=True, 
        style={'base_template': 'rich_textarea.html', 'rows': 5},
        error_messages={
            "required": "Description is required.",
        },
    )
    status = serializers.ChoiceField(
        choices=PRODUCT_STATUS_CHOICES,  # Assuming you've defined PRODUCT_STATUS_CHOICES
        required=True,
        style={'base_template': 'custom_select.html','custom_class':'col-6'},
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
    )
    
    units = serializers.ChoiceField(
        label=('Units'),
        choices=UNIT_CHOICES, 
        required=True,
        style={
            'base_template': 'custom_select.html',
            'custom_class':'col-6'
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
        child=serializers.FileField(allow_empty_file=False,use_url=False ),
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
            'accept': ','.join(settings.IMAG_SUPPORTED_EXTENSIONS),  # Set the accepted file extensions
            'allow_null': True,  # Allow None values
        },
        help_text=('Supported file extensions: ' + ', '.join(settings.IMAG_SUPPORTED_EXTENSIONS))
        )
    def validate_item_name(self, value):
        # Check for minimum length of 3 characters
        if len(value) < 3:
            raise serializers.ValidationError("Item Name must be at least 3 characters long.")

        # Check for special characters
        if not re.match(r'^[a-zA-Z0-9\s]*$', value):
            raise serializers.ValidationError("Item Name can only contain alphanumeric characters and spaces.")

        return value
    def validate_reference_number(self, value):
        """
        Validate that the reference number (SKU) is unique.
        """
        if self.instance and self.instance.reference_number == value:
            return value  # No need to check for uniqueness if updating the same instance

        if Item.objects.filter(reference_number=value).exists():
            raise serializers.ValidationError("This reference number reference number is already in use.")
        
        return value

    class Meta:
        model = Item
        fields = ['item_name','category_id','price', 'description', 'units', 'quantity_per_box','reference_number','status','file_list']

