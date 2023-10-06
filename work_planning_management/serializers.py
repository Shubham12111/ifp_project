from rest_framework import serializers
from requirement_management.models import Quotation  
from authentication.models import User

class QuotationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quotation
        fields = '__all__'

