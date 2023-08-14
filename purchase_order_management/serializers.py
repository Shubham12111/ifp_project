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