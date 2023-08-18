from .models import *
from django.db import transaction
from rest_framework import serializers
from infinity_fire_solutions.custom_form_validation import *

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
        fields = ['id','po_number', 'vendor_id', 'inventory_location_id', 'order_date', 'due_date', 'sub_total', 'discount', 'tax','total_amount','status']

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
    order_date = serializers.DateField(
        required=True,
        error_messages={
            "required": "Order date is required.",
            "blank": "Order date is required.",
            "invalid": "Invalid order date format. Use one of these formats instead: DD-MM-YYYY",
            # You can add more error messages as needed
        }
    )
    
    due_date = serializers.DateField(
        required=True,
        error_messages={
            "required": "Due date is required.",
            "blank": "Due date is required.",
            "invalid": "Invalid due date format. Use one of these formats instead: DD-MM-YYYY",
            # You can add more error messages as needed
        }
    )

    class Meta:
        model = PurchaseOrder
        fields = ['po_number', 'vendor_id', 'inventory_location_id', 'order_date', 'due_date', 'sub_total', 'discount', 'tax','total_amount','notes','status', "approval_notes"]


    def validate_sub_total(self, value):
        if value < 0:
            raise serializers.ValidationError("Sub Total must be a positive value.")
        return value

    def validate_discount(self, value):
        if value < 0:
            raise serializers.ValidationError("Discount must be a positive value.")
        return value

    def validate_tax(self, value):
        if value < 0:
            raise serializers.ValidationError("Tax must be a positive value.")
        return value

    def validate_total_amount(self, value):
        if value < 0:
            raise serializers.ValidationError("Total Amount must be a positive value.")
        return value