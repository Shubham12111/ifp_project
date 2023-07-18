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

class SignupSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        label=('Name *'),
        max_length=100,
        style={
            "input_type": "text",
            "autofocus": True,
            "autocomplete": "off",
            "required": True,
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Name field cannot be blank.",
        },
    )
    
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
    confirm_password = serializers.CharField(
        label=('Confirm Password *'),
        max_length=100,
        style={
            "input_type": "password",
            "autofocus": True,
            "autocomplete": "off",
            "required": True,
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Confirm Password field cannot be blank.",
        },
    )

    def validate(self, data):
        password = data.get('password')
        confirm_password = data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})

        return data

    def validate_email(self, value):
        # Call the parent's is_valid() method to perform the default validationif 
        if value:
            user_email = User.objects.filter(email=value).exists()
            if user_email:
                raise serializers.ValidationError('User with this email already exists, Please try with differnt email.')
        return value

    class Meta:
        model = User
        fields = ('name', 'email', 'password', 'confirm_password')

class ForgotPasswordSerializer(serializers.Serializer):
    
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

    class Meta:
        fields = ('email')

class VerifyOTPSerializer(serializers.Serializer):
    
    otp = serializers.CharField(
        label=('OTP *'),
        max_length=100,
        style={
            "input_type": "text",
            "autofocus": True,
            "autocomplete": "off",
            "required": True,
        },
        error_messages={
            "required": "This field is required.",
            "blank": "OTP cannot be blank.",
        },
    )

    class Meta:
        fields = ('otp')