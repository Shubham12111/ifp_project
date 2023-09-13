import uuid
from .models import *
from django.db import transaction
from rest_framework import serializers
from infinity_fire_solutions.aws_helper import *
from infinity_fire_solutions.custom_form_validation import *
from django.conf import settings
from stock_management.models import Item
from django.utils.translation import gettext as _


def validate_non_negative(value):
    if value < 0:
        raise ValidationError("Value cannot be negative.")


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
    allowed_extensions= ["png", "jpg", "jpeg","pdf"],
    message=('Unsupported file extension. Please upload a valid file.'),
)

class InventoryLocationSerializer(serializers.ModelSerializer):
    full_address = serializers.SerializerMethodField()  # New field for combined address

    class Meta:
        model = InventoryLocation
        fields = ['name', 'description', 'address', 'country', 'town', 'county', 'post_code', 'full_address']

    def get_full_address(self, instance):
        # Combine address components into a single string
        address_components = [
            instance.address,
            instance.town.name,
            instance.county.name,
            instance.post_code,
            instance.country.name
        ]
        full_address = ', '.join(filter(None, address_components))  # Join non-empty components with ', '

        return full_address

class PurchaseOrderListSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = PurchaseOrder
        fields = ['id','po_number', 'vendor_id', 'inventory_location_id','created_at', 'sub_total', 'discount', 'tax','total_amount','status']

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if instance.vendor_id:
            vendor = instance.vendor_id
            vendor_name = f"{vendor.first_name} {vendor.last_name}"
            vendor_email = vendor.email 
            representation['vendor_id'] = f"{vendor_name}"

        representation['inventory_location_id'] = f'{instance.inventory_location_id.name}'

        return representation
    
class PurchaseOrderSerializer(serializers.ModelSerializer):
    inventory_location_id = serializers.PrimaryKeyRelatedField(
        required=True,
        queryset=InventoryLocation.objects.all(),
        error_messages={
            "required": "This field is required.",
            "blank": "Inventory Location is required.",
            "incorrect_type":"Inventory Location is required.",
            "null": "Inventory Location is required."
        },
    )
    vendor_id = serializers.PrimaryKeyRelatedField(
        required=True,
        queryset=Vendor.objects.all(),
        error_messages={
            "required": "This field is required.",
            "blank": "Vendor is required.",
            "incorrect_type":"Vendor is required.",
            "null": "Vendor is required."
        },
    )
    

    file = serializers.FileField(
    required=False,
    validators=[file_extension_validator, validate_file_size],
    )  

    discount = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        required=False,
        validators=[validate_non_negative]    # Apply MinValueValidator
    )
    tax = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        required=False,
        validators=[validate_non_negative]  # Apply MinValueValidator
    )

    class Meta:
        model = PurchaseOrder
        fields = ['vendor_id', 'inventory_location_id',  'sub_total', 'discount', 'tax','total_amount','notes','status', "approval_notes",'file']


    def validate_sub_total(self, value):
        if value < 0:
            raise serializers.ValidationError("Sub Total must be a positive value.")
        return value


    def validate_total_amount(self, value):
        if value < 0:
            raise serializers.ValidationError("Total Amount must be a positive value.")
        return value
    
    def create(self, validated_data):
        # Pop the 'file' field from validated_data
        file = validated_data.pop('file', None)

        # Create a new instance of Conversation with 'title' and 'message'
        instance = PurchaseOrder.objects.create(**validated_data)

        if file:
            # Generate a unique filename
            unique_filename = f"{str(uuid.uuid4())}_{file.name}"
            upload_file_to_s3(unique_filename, file, 'purchase_order')
            instance.document = f'purchase_order/{unique_filename}'
            instance.save()

        return instance
    
    def update(self, instance, validated_data):
        file = validated_data.pop('file', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        with transaction.atomic():
            instance.save()

        if file:
            # Generate a unique filename
            unique_filename = f"{str(uuid.uuid4())}_{file.name}"
            upload_file_to_s3(unique_filename, file, 'purchase_order')
            instance.document = f'purchase_order/{unique_filename}'
            instance.save()

        return instance

class PurchaseOrderReceivedInventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrderReceivedInventory
        fields = ['purchase_order_item_id','received_inventory']


def validate_invoice_file_size(value):
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
invoice_file_extension_validator = FileExtensionValidator(
    allowed_extensions=['pdf'],
    message=('Unsupported file extension. Please upload a valid file.'),
)

class PurchaseOrderInvoiceSerializer(serializers.ModelSerializer):
    invoice_date = serializers.DateField(
        required=True,
        error_messages={
            "required": "Invoice date is required.",
            "blank": "Invoice date is required.",
            "invalid": "Invalid due date format. Use one of these formats instead: YYYY-MM-DD",
            # You can add more error messages as needed
        }
    )
    invoice_number = serializers.CharField(
        required=True, 
        error_messages={
            "required": "Invoice Number field is required.",
            "blank": "Invoice Number is required.",
        },
    )
     
    file = serializers.FileField(
    required=False,
    validators=[invoice_file_extension_validator, validate_invoice_file_size],
    )
    class Meta:
        model = PurchaseOrderInvoice
        fields = ['invoice_number', 'invoice_date', 'comments','file']
    

    def validate_invoice_number(self, value):
        """
        Validate that the invoice_number is unique.
        """
        if self.instance:
            invoice_number = PurchaseOrderInvoice.objects.filter(invoice_number__exact=value).exclude(id=self.instance.id).exists()
        else:
            invoice_number = PurchaseOrderInvoice.objects.filter(invoice_number__exact=value).exists()
        
        if invoice_number:
            raise serializers.ValidationError("This invoice number is already in use.")
        
        return value

    def create(self, validated_data):
        # Pop the 'file' field from validated_data
        file = validated_data.pop('file', None)

        # Create a new instance of Conversation with 'title' and 'message'
        instance = PurchaseOrderInvoice.objects.create(**validated_data)

        if file:
            # Generate a unique filename
            unique_filename = f"{str(uuid.uuid4())}_{file.name}"
            upload_file_to_s3(unique_filename, file, 'purchase_order/invoice')
            instance.invoice_pdf_path = f'purchase_order/invoice/{unique_filename}'
            instance.save()

        return instance
    
    def update(self, instance, validated_data):
        file = validated_data.pop('file', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        with transaction.atomic():
            instance.save()

        if file:
            # Generate a unique filename
            unique_filename = f"{str(uuid.uuid4())}_{file.name}"
            upload_file_to_s3(unique_filename, file, 'purchase_order/invoice')
            instance.invoice_pdf_path = f'purchase_order/invoice/{unique_filename}'
            instance.save()

        return instance

class ItemSerializer(serializers.ModelSerializer):
     class Meta:
        model = Item
        fields = ['id','item_name','category_id','price', 'description', 'units', 'quantity_per_box','reference_number']
            