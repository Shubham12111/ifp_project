
from rest_framework import serializers
from authentication.models import User


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'company_name')