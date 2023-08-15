from .models import *
from django.db import transaction
from rest_framework import serializers


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

class PurchaseOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrder
        fields = ['po_number', 'vendor_id', 'inventory_location_id', 'order_date', 'due_date', 'sub_total', 'discount', 'tax','total_amount','notes','status']
        

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