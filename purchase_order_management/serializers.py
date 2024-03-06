import json
import uuid
from .models import *
from django.db import transaction
from rest_framework import serializers
from infinity_fire_solutions.aws_helper import *
from infinity_fire_solutions.custom_form_validation import *
from django.conf import settings
from stock_management.models import Item
from django.utils.translation import gettext as _
from authentication.models import User
from django.utils import timezone
from rest_framework.serializers import ValidationError


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
            instance.town,
            instance.county,
            instance.post_code,
            instance.country
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

class PurchaseOrderItemsSerializer(serializers.ModelSerializer):

    item = serializers.PrimaryKeyRelatedField(
        queryset = Item.objects.all(),
        required = False,
        allow_empty = True,
        allow_null = True
    )

    reference_number = serializers.CharField(
        allow_null = True,
        allow_blank = True,
        required = False,
        max_length = 49
    )

    class Meta:
        model = PurchaseOrderItem
        fields = [
            'id',
            'item',
            'item_json',
            'item_name',
            'reference_number',
            'quantity',
            'unit_price',
            'row_total',
        ]
    
    def to_internal_value(self, data):
        """
        Convert the incoming validated data into a suitable internal representation.

        Args:
            data (any): The incoming validated data.

        Returns:
            any: The converted internal representation of the data.
        """
        # If data is a list of strings representing JSON objects, deserialize them
        if isinstance(data, list) and all(isinstance(item, str) for item in data):
            return [json.loads(item) for item in data]
        
        if isinstance(data, str):
            return json.loads(data)
        
        # Otherwise, let the parent class handle the conversion
        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['item'] = ret['item'] if instance.item else ''
        return ret

class PurchaseOrderSerializer(serializers.ModelSerializer):
    
    location_type = serializers.ChoiceField(
        choices=LOCATION_TYPE_CHOICES,
        default='warehouse'
    )

    inventory_location_id = serializers.PrimaryKeyRelatedField(
        required=False,
        queryset=InventoryLocation.objects.all(),
        error_messages={
            "required": "This field is required.",
            "blank": "Inventory Location is required.",
            "incorrect_type":"Inventory Location is required.",
            "null": "Inventory Location is required."
        },
    )

    user_id = serializers.PrimaryKeyRelatedField(
        required=False,
        queryset=User.objects.all(),
        error_messages={
            "required": "This field is required.",
            "blank": "Inventory Location is required.",
            "incorrect_type":"Inventory Location is required.",
            "null": "Inventory Location is required."
        },
    )

    site_address = serializers.PrimaryKeyRelatedField(
        required=False,
        queryset=SiteAddress.objects.all(),
        error_messages={
            "required": "This field is required.",
            "blank": "Site Address is required.",
            "incorrect_type":"Site Address is required.",
            "null": "This field is required."
        },
    )
    
    po_for = serializers.ChoiceField(
        choices=POFOR_TYPE_CHOICES,
        default='vendor'
    )

    vendor_id = serializers.PrimaryKeyRelatedField(
        required=False,
        queryset=Vendor.objects.all(),
        error_messages={
            "required": "This field is required.",
            "blank": "Vendor is required.",
            "incorrect_type":"Vendor is required.",
            "null": "Vendor is required."
        },
    )

    sub_contractor_id = serializers.PrimaryKeyRelatedField(
        required=False,
        queryset=Contact.objects.filter(contact_type__name='Sub-Contractor').all(),
        error_messages={
            "required": "This field is required.",
            "blank": "Sub-Contractor is required.",
            "incorrect_type":"Sub-Contractor is required.",
            "null": "Sub-Contractor is required."
        },
    )

    job_id = serializers.PrimaryKeyRelatedField(
        required=False,
        queryset=Job.objects.filter(status__in=['planned', 'in-progress']).all(),
        error_messages={
            "required": "This field is required.",
            "blank": "Job is required.",
            "incorrect_type":"Job is required.",
            "null": "Job is required."
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

    po_date = serializers.DateField(
        default=timezone.now().date(),
        input_formats=["%d/%m/%Y"]
    )

    po_due_date = serializers.DateField(
        input_formats=["%d/%m/%Y"],
        required=True
    )

    items = serializers.ListField(
        child=PurchaseOrderItemsSerializer()
    )

    class Meta:
        model = PurchaseOrder
        fields = [
            # PO For
            'po_for', 'vendor_id', 'sub_contractor_id', 'job_id',

            # PO Recive Location 
            'location_type', 'inventory_location_id', 'user_id', 'site_address',

            # PO Prices
            'sub_total', 'discount', 'tax', 'total_amount', 

            # PO Approvals, Notes, and Files
            'notes', 'status', "approval_notes", 'file', 

            # PO Dates
            'po_date', 'po_due_date',

            "items"
        ]

    def __validate_locations__(self, attrs) -> None:
        """
        Validate locations based on location_type.
        
        Args:
            attrs (dict): The attributes to validate.

        Raises:
            serializers.ValidationError: If validation fails.
        """
        location_type = attrs.get('location_type', 'warehouse')
        site_address = attrs.get('site_address', None)
        user_id = attrs.get('user_id', None)
        inventory_location_id = attrs.get('inventory_location_id', None)

        if location_type == 'warehouse':
            if not inventory_location_id:
                raise serializers.ValidationError({
                    'inventory_location_id': ['Please select an Inventory Location.'],
                })

        else:
            if site_address and user_id:
                if site_address.user_id not in [user_id]:
                    raise serializers.ValidationError({
                        'site_address': ['The selected Site Address does not match the Customer Site Address.']
                    })

            if site_address and not user_id:
                raise serializers.ValidationError({
                    'user_id': ['Please select a Customer before choosing a Site Address.']
                })

            if user_id and not site_address:
                raise serializers.ValidationError({
                    'site_address': ['Please select a Site Address for the chosen customer.']
                })

        if not inventory_location_id and not site_address:
            raise serializers.ValidationError({
                'site_address': ['Please choose either an Inventory Location or a Site Address of a Customer.'],
                'inventory_location_id': ['Please choose either an Inventory Location or a Site Address of a Customer.'],
            })

    def __validate_order_for__(self, attrs) -> None:
        """
        Validate order based on po_for.
        
        Args:
            attrs (dict): The attributes to validate.

        Raises:
            serializers.ValidationError: If validation fails.
        """
        po_for = attrs.get('po_for', 'vendor')
        sub_contractor_id = attrs.get('sub_contractor_id', None)
        job_id = attrs.get('job_id', None)
        vendor_id = attrs.get('vendor_id', None)

        if po_for == 'vendor':
            if not vendor_id:
                raise serializers.ValidationError({
                    'vendor_id': ['Please select a Vendor.'],
                })
        else:
            if not job_id:
                raise serializers.ValidationError({
                    'job_id': ['Please select a Job.']
                })

            if not sub_contractor_id:
                raise serializers.ValidationError({
                    'sub_contractor_id': ['Please select a Sub-Contractor.']
                })

        if not vendor_id and (not sub_contractor_id or not job_id):
            raise serializers.ValidationError({
                'job_id': ['Please choose either a Vendor or a Sub-Contractor and Job.'],
                'sub_contractor_id': ['Please choose either a Vendor or a Sub-Contractor and Job.'],
                'vendor_id': ['Please choose either a Vendor or a Sub-Contractor and Job.'],
            })

    def validate(self, attrs):
        self.__validate_locations__(attrs)
        self.__validate_order_for__(attrs)

        po_date = attrs.get('po_date', timezone.now().date())
        po_due_date = attrs.get('po_due_date', None)

        if not po_due_date:
            raise serializers.ValidationError(
                {'po_due_date': ['Due Date is required.']}
            )
        
        if po_due_date <= po_date:
            raise serializers.ValidationError(
                {'po_due_date': ['Due Date must be greater than the PO Date.']}
            )

        return attrs


    def validate_sub_total(self, value):
        """
        Validate the sub total value.

        Args:
            value (float): The sub total value to validate.

        Returns:
            float: The validated sub total value.

        Raises:
            serializers.ValidationError: If the sub total value is negative.
        """
        # Check if the sub total is negative
        if value < 0:
            raise serializers.ValidationError("Sub Total must be a positive value.")
        return value

    def validate_total_amount(self, value):
        """
        Validate the total amount value.

        Args:
            value (float): The total amount value to validate.

        Returns:
            float: The validated total amount value.

        Raises:
            serializers.ValidationError: If the total amount value is negative.
        """
        # Check if the total amount is negative
        if value < 0:
            raise serializers.ValidationError("Total Amount must be a positive value.")
        return value
    
    def create(self, validated_data):
        """
        Create a new purchase order instance.

        Args:
            validated_data (dict): Validated data for creating a purchase order.

        Returns:
            instance: Created purchase order instance.
        """
        # Pop the 'file' field from validated_data
        file = validated_data.pop('file', None)

        # Pop the 'items' field from the validated_data
        items = validated_data.pop('items', [])

        if not items:
            raise serializers.ValidationError(
                {'itemTableBody': ['Items are required to create a purchase order.']}
            )

        # Create a new instance of Conversation with 'title' and 'message'
        instance = PurchaseOrder.objects.create(**validated_data)

        items_serializer = PurchaseOrderItemsSerializer(data=items, many=True)
        if not items_serializer.is_valid():
            instance.delete()
            raise serializers.ValidationError(
                {'itemTableBody': ['Unable to save the items, try again later']}
            )

        items_serializer.save(purchase_order_id=instance)

        if file:
            # Generate a unique filename
            unique_filename = f"{str(uuid.uuid4())}_{file.name}"
            upload_file_to_s3(unique_filename, file, 'purchase_order')
            instance.document = f'purchase_order/{unique_filename}'
            instance.save()

        return instance

    def update(self, instance, validated_data):
        """
        Update an existing purchase order instance.

        Args:
            instance (PurchaseOrder): Existing purchase order instance.
            validated_data (dict): Validated data for updating the purchase order.

        Returns:
            instance: Updated purchase order instance.
        """
        file = validated_data.pop('file', None)

        # Pop the 'items' field from the validated_data
        items = validated_data.pop('items', [])

        if not items:
            raise serializers.ValidationError(
                {'itemTableBody': ['Items are required to create a purchase order.']}
            )

        items_serializer = PurchaseOrderItemsSerializer(data=items, many=True)

        if not items_serializer.is_valid():
            instance.delete()
            raise serializers.ValidationError(
                {'itemTableBody': ['Unable to save the items, try again later']}
            )

        existing_items = PurchaseOrderItem.objects.filter(purchase_order_id=instance).all()
        existing_items.delete()
        items_serializer.save(purchase_order_id=instance)

        if instance.po_date:
            validated_data.pop('po_date', '')

        instance = super().update(instance, validated_data)

        if file:
            # Generate a unique filename
            unique_filename = f"{str(uuid.uuid4())}_{file.name}"
            upload_file_to_s3(unique_filename, file, 'purchase_order')
            instance.document = f'purchase_order/{unique_filename}'
            instance.save()

        return instance

    def to_representation(self, instance):
        """
        Serialize the purchase order instance into a representation.

        Args:
            instance (PurchaseOrder): Purchase order instance.

        Returns:
            dict: Serialized representation of the purchase order instance.
        """
        ret = {}
        items = PurchaseOrderItemsSerializer(
            PurchaseOrderItem.objects.filter(purchase_order_id=instance).all(),
            many=True
        ).data
        
        ret.update({
            'vendor_id': instance.vendor_id.id if instance.vendor_id else '',
            'inventory_location_id': instance.inventory_location_id.id if instance.inventory_location_id else '',
            'user_id': instance.user_id.id if instance.user_id else '',
            'site_address': instance.site_address.id if instance.site_address else '',
            'po_number': instance.po_number,
            'created_at': instance.created_at.strftime('%Y-%m-%d'),  # Convert date to string
            'tax': instance.tax,
            'sub_total': instance.sub_total,
            'discount': instance.discount,
            'notes': instance.notes,
            'grand_total': instance.total_amount,
            'location_type': instance.location_type,
            'po_for': instance.po_for,
            'sub_contractor_id': instance.sub_contractor_id.id if instance.sub_contractor_id else '',
            'job_id': instance.job_id.id if instance.job_id else '',
            'po_due_date': instance.po_due_date.strftime("%d/%m/%Y") if instance.po_due_date else '',
            'po_date': instance.po_date.strftime("%d/%m/%Y") if instance.po_date else timezone.now().date().strftime("%d/%m/%Y"),
            'items': items,
        })
        
        if instance.document:
            ret['presigned_url'] = generate_presigned_url(instance.document),
            ret['file_name'] =  instance.document.split('/')[-1]

        return ret

class PurchaseOrderViewSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = PurchaseOrder
        fields = '__all__'

    def to_representation(self, instance):
        """
        Serialize the purchase order instance into a representation.

        Args:
            instance (PurchaseOrder): Purchase order instance.

        Returns:
            dict: Serialized representation of the purchase order instance.
        """
        ret = {}
        items = PurchaseOrderItemsSerializer(
            PurchaseOrderItem.objects.filter(purchase_order_id=instance).all(),
            many=True
        ).data
        
        ret.update({
            'id': instance.id,

            'po_for': instance.get_po_for_display(),
            'vendor_id': {
                'id': instance.vendor_id.id, 
                'name': f'{instance.vendor_id.first_name} {instance.vendor_id.last_name}',
                'email': f'{instance.vendor_id.email}',
                'phone_number': f'{instance.vendor_id.phone_number}'
            } if instance.vendor_id else '',
            'sub_contractor_id': {
                'id': instance.sub_contractor_id.id, 
                'name': f'{instance.sub_contractor_id.first_name} {instance.sub_contractor_id.last_name}',
                'email': f'{instance.sub_contractor_id.email}',
                'phone_number': f'{instance.sub_contractor_id.phone_number}'
            } if instance.sub_contractor_id else '',


            'location_type': instance.get_location_type_display(),
            'inventory_location_id': { 
                'id': instance.inventory_location_id.id,
                'name': instance.inventory_location_id.name,
                'address': f'{instance.inventory_location_id.address}{", " if instance.inventory_location_id.town else ""} {instance.inventory_location_id.town}{", " if instance.inventory_location_id.county else ""} {instance.inventory_location_id.county}{", " if instance.inventory_location_id.country else ""} {instance.inventory_location_id.country}{", " if instance.inventory_location_id.post_code else ""} {instance.inventory_location_id.post_code}', 
            } if instance.inventory_location_id else "",
            'site_address': { 
                'id': instance.site_address.id,
                'name': instance.site_address.site_name,
                'address': f'{instance.site_address.address}{", " if instance.site_address.town else ""} {instance.site_address.town}{", " if instance.site_address.county else ""} {instance.site_address.county}{", " if instance.site_address.country else ""} {instance.site_address.country}{", " if instance.site_address.post_code else ""} {instance.site_address.post_code}', 
            } if instance.site_address else "",
            'user_id': {
                'id': instance.user_id.id, 
                'name': f'{instance.user_id.customermeta.company_name}' if instance.user_id.customermeta else '',
                'email': f'{instance.user_id.customermeta.email}' if instance.user_id.customermeta else ''
            } if instance.user_id else '',
            
            'status': instance.get_status_display(),

            'po_number': instance.po_number,
            'tax': instance.tax,
            'tax_price': round((instance.tax / 100) * instance.sub_total, 2) if instance.tax and instance.sub_total else 00.00,
            'sub_total': instance.sub_total,
            'discount': instance.discount,
            'notes': instance.notes,
            'approval_notes': instance.approval_notes,
            'total_amount': instance.total_amount,
            
            'po_due_date': instance.po_due_date.strftime("%d/%m/%Y") if instance.po_due_date else '',
            'po_date': instance.po_date.strftime("%d/%m/%Y") if instance.po_date else timezone.now().date().strftime("%d/%m/%Y"),
            
            'items': items,
            'created_at': instance.created_at.strftime('%Y-%m-%d'),  # Convert date to string
            
            'job_id': instance.job_id.id if instance.job_id else '',
        })
        
        if instance.document:
            presigned_url = generate_presigned_url(instance.document),
            file_name = instance.document.split('/')[-1]
            if presigned_url and file_name:
                ret['document'] = {'url':presigned_url, 'name':file_name}

        return ret


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

class PurchaseOrderReceivedInventorySerializer(serializers.ModelSerializer):

    purchase_order_item_id = serializers.PrimaryKeyRelatedField(
        queryset = PurchaseOrderItem.objects.all(),
        required=True
    )

    received_inventory = serializers.IntegerField(
        min_value = 0,
        required=True,
        error_messages={
            "required": "Quantity field is required.",
            "blank": "Quantity is required.",
        },
    )

    class Meta:
        model = PurchaseOrderReceivedInventory
        fields = ['purchase_order_item_id', 'received_inventory']
    
    def to_internal_value(self, data):
        """
        Convert the incoming validated data into a suitable internal representation.

        Args:
            data (any): The incoming validated data.

        Returns:
            any: The converted internal representation of the data.
        """
        # If data is a list of strings representing JSON objects, deserialize them
        if isinstance(data, list) and all(isinstance(item, str) for item in data):
            return [json.loads(item) for item in data]
        
        if isinstance(data, str):
            return json.loads(data)
        
        # Otherwise, let the parent class handle the conversion
        return super().to_internal_value(data)

class PurchaseOrderInvoiceSerializer(serializers.ModelSerializer):
    invoice_date = serializers.DateField(
        required=True,
        input_formats=['%d/%m/%Y'],
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

    purchase_order_items = serializers.ListField(
        child=PurchaseOrderReceivedInventorySerializer()
    )

    class Meta:
        model = PurchaseOrderInvoice
        fields = ['invoice_number', 'invoice_date', 'comments', 'file', 'purchase_order_items']
    

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

        # Pop the 'items' field from the validated_data
        purchase_order_items = validated_data.pop('purchase_order_items', [])

        if not purchase_order_items:
            raise serializers.ValidationError(
                {'purchase_order_items': ['Items are required to create a purchase order.']}
            )

        # Create a new instance of Conversation with 'title' and 'message'
        instance = super().create(validated_data)

        items_serializer = PurchaseOrderReceivedInventorySerializer(data=purchase_order_items[0], many=True)
        if not items_serializer.is_valid():
            instance.delete()
            raise serializers.ValidationError(
                {'purchase_order_items': items_serializer.errors}
            )

        inventory = items_serializer.save(purchase_order_invoice_id=instance)
        
        purchase_order = instance.purchase_order_id
        partially_completed_inventory = [inv for inv in inventory if inv.purchase_order_item_id.quantity != inv.received_inventory ]
        if partially_completed_inventory:
            purchase_order.status = 'partially_completed'
        else:
            purchase_order.status = 'completed'
        
        purchase_order.save()

        if file:
            # Generate a unique filename
            unique_filename = f"{str(uuid.uuid4())}_{file.name}"
            upload_file_to_s3(unique_filename, file, 'purchase_order/invoice')
            instance.invoice_pdf_path = f'purchase_order/invoice/{unique_filename}'
            instance.save()

        return instance
    
    def update(self, instance, validated_data):
        file = validated_data.pop('file', None)

        instance = super().update(instance, validated_data)

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
            