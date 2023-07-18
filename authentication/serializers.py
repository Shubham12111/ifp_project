from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User


class LoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        label=('Email *'),
        max_length=100,
        style={
            "input_type": "email",
            "autofocus": True,
            "autocomplete": "off",
            "required": True,
            
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Email field cannot be blank.",
        },
    )
    password = serializers.CharField(
        label=('Password *'),
        max_length=100,
        style={
            "input_type": "password",
            "autofocus": True,
            "autocomplete": "off",
            "required": True,
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Password field cannot be blank.",
        },
    )

    class Meta:
        model = User
        fields = ('email', 'password')
