from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from infinity_fire_solutions.custom_form_validation import *
from .models import *
import re

class VendorSerializer(serializers.ModelSerializer):
    """
    Serializer for the Vendor model.
    """
    
    first_name = serializers.CharField(
        label=('First Name '),
        required=True,
        max_length=100,
        style={
            "input_type": "text",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
            'base_template': 'custom_input.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "First Name is required.",
            "invalid": "First Name can only contain characters.",
        },
    )


    class Meta:
        model = Vendor
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'company')

    def validate_first_name(self, value):
        """
        Custom validation for the first name field.
        """
        if not re.match(r'^[a-zA-Z\s]+$', value):
            raise serializers.ValidationError("Invalid First Name. Only alphabets and spaces are allowed.")

        if len(value) < 2:
            raise serializers.ValidationError("First Name should be at least 2 characters long.")

        return value


class BillingDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for the BillingDetail model.
    """

    # Field definitions...

    class Meta:
        model = Vendor 
        fields = ('vat_number', 'tax_preference', 'address', 'town', 'county', 'country', 'post_code')

    def validate_vat_number(self, value):
        """
        Custom validation for the VAT number field.
        """
        if not re.match(r'^\d{9}$', value):
            raise serializers.ValidationError("Invalid VAT number format. It should be a 9-digit number.")
        if int(value) == 0:
            raise serializers.ValidationError("Only zeros are not allowed in VAT Number")
        return value


class VendorContactPersonSerializer(serializers.ModelSerializer):
    """
    Serializer for the VendorContactPerson model.
    """

    # Field definitions...

    class Meta:
        model = VendorContactPerson
        fields = ['salutation', 'first_name', 'last_name', 'email', 'phone_number']

class VendorRemarkSerializer(serializers.ModelSerializer):
    """
    Serializer for the VendorRemark model.
    """

    remarks = serializers.CharField(
        label=' ',
        max_length=255,
        required=False,
        allow_blank=True,
        allow_null=True,
        style={
           'base_template': 'rich_textarea.html',
        },
    )

    class Meta:
        model = Vendor
        fields = ['remarks']
