from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User

class LoginSerializer(serializers.ModelSerializer):
    """
    Serializer class for user login.
    """

    email = serializers.EmailField(
        label=('Email *'),
        max_length=100,
        style={
            "input_type": "email",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
            "autofocus": False,
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
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
            "autofocus": False,
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
    first_name = serializers.CharField(
        label=('First Name *'),
        max_length=100,
        style={
            "input_type": "text",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
            "autofocus": False,
        },
        error_messages={
            "required": "This field is required.",
            "blank": "First Name field cannot be blank.",
        },
    )
    
    last_name = serializers.CharField(
        label=('Last Name *'),
        max_length=100,
        style={
            "input_type": "text",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
            "autofocus": False,
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Last Name field cannot be blank.",
        },
    )
    
    email = serializers.EmailField(
        label=('Email *'),
        max_length=100,
        style={
            "input_type": "email",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
            "autofocus": False,
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
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
            "autofocus": False,
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Password field cannot be blank.",
        },
    )
    
    password2 = serializers.CharField(
        label=('Confirm Password *'),
        max_length=100,
        style={
            "input_type": "password",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
            "autofocus": False,
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Confirm Password field cannot be blank.",
        },
        write_only=True
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password', 'password2')
        
    def validate(self, data):
        password = data.get('password')
        confirm_password = data.get('password2')

        if password and confirm_password and password != confirm_password:
            raise serializers.ValidationError({"password2": "Passwords do not match."})

        return data

    def validate_email(self, value):
        # Call the parent's is_valid() method to perform the default validationif 
        if value:
            user_email = User.objects.filter(email=value).exists()
            if user_email:
                raise serializers.ValidationError('User with this email already exists, Please try with differnt email.')
        return value

    def create(self, validate_data):
        validate_data.pop('password2')
        return User.objects.create_user(**validate_data)

class ForgotPasswordSerializer(serializers.Serializer):
    
    email = serializers.EmailField(
        label=('Email *'),
        max_length=100,
        style={
            "input_type": "email",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
            "autofocus": False,
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
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
            "autofocus": False,
        },
        error_messages={
            "required": "This field is required.",
            "blank": "OTP cannot be blank.",
        },
    )

    class Meta:
        fields = ('otp')