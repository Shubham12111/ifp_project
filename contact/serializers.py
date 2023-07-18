from rest_framework import serializers
from .models import Contact

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['name', 'email', 'phone_number', 'contact_type','job_title','company','address','city','country','state','pincode','created_at','updated_at']

        # Specify the required fields using the required=True argument
        extra_kwargs = {
            'name': {'required': True},
            'email': {'required': True},
            'phone_number': {'required': True},
            'contact_type': {'required': True},
        }
