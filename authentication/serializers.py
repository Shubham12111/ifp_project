from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework.renderers import HTMLFormRenderer

from cities_light.models import City, Country, Region
from .models import User
import re


def custom_validate_password(value):
    if 'password' in value.lower():
        raise serializers.ValidationError({"password":'Password should not contain the word "password".'})
    if len(value) < 8:
        raise serializers.ValidationError({"password":'Password should be at least 8 characters long.'})
    if not re.findall(r'\d', value):
        raise serializers.ValidationError({"password":'The password must contain at least 1 digit.'})
    if not re.findall(r'[A-Z]', value):
        raise serializers.ValidationError({"password":'The password must contain at least 1 uppercase letter.'})
    if not re.findall(r'[()[\]{}|\\`~!@#$%^&*_\-+=;:\'",<>./?]', value):
        raise serializers.ValidationError({"password":'Password should contain a symbol.'})
    if not re.findall(r'[a-z]', value):
        raise serializers.ValidationError({"password":'The password must contain at least 1 lowercase letter (a-z).'})
    return value


def phone_number_validator(value):
    # Define your phone number validation regex pattern
    pattern = r'^\d{1,14}$'
    
    # Validate the phone number format using the regex pattern
    if not re.match(pattern, value):
        raise serializers.ValidationError('Invalid phone number format.')
    return value
    
def pincode_validator(value):
    if not value.isdigit() or len(value) != 6:
        raise serializers.ValidationError('Invalid pincode format.')
    return value
    

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
            "blank": "Email is required.",
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
            "blank": "Password is required.",
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
            'base_template': 'custom_input.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "First Name is required.",
             "invalid": "Last Name can only contain characters.",
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
            'base_template': 'custom_input.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Last Name is required.",
            "invalid": "Last Name can only contain characters.",
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
            "blank": "Email is required.",
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
            "blank": "Password is required.",
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
            "blank": "Confirm Password is required.",
        },
        write_only=True
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password', 'password2')
        
    def validate(self, data):
        custom_validate_password(data.get('password'))
        
        password = data.get('password')
        confirm_password = data.get('password2')

        if password and confirm_password and password != confirm_password:
            raise serializers.ValidationError({"password2": "Passwords do not match."})

        return data
    
    def validate_last_name(self, value):
        if not re.match(r'^[a-zA-Z]+$', value):
            raise serializers.ValidationError("Last Name can only contain characters.")
        return value
    
    def validate_first_name(self, value):
        if not re.match(r'^[a-zA-Z]+$', value):
            raise serializers.ValidationError("Last Name can only contain characters.")
        return value


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
            "blank": "Email is required.",
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
        



class UserProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(
        max_length=100,
        label='First Name *',
        error_messages={
            "required": "This field is required.",
            "blank": "First Name is required.",
            "invalid": "First Name can only contain characters.",
        },
        style={
            "input_type": "text",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
            "autofocus": False,
            'base_template': 'custom_input.html'
        },
    )
    last_name = serializers.CharField(
        max_length=100,
        label='Last Name *',
        error_messages={
            "required": "This field is required.",
            "blank": "Last Name is required.",
            "invalid": "Last Name can only contain characters.",
        },
        style={
            "input_type": "text",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
            "autofocus": False,
            'base_template': 'custom_input.html'
        },
    )
    
    email = serializers.EmailField(
        max_length=100,
        label='Email (Editing the email address is currently not supported.)',
        
        error_messages={
            "required": "This field is required.",
            "blank": "Email is required.",
        },
        style={
            'base_template': 'custom_email.html'
        },
    )
    phone_number = serializers.CharField(
        max_length=14,
        required=False,
        validators=[phone_number_validator],
        style={
            'base_template': 'custom_input.html'
        },
    )
    
    address = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        allow_null=True,
        
    )
    country = serializers.PrimaryKeyRelatedField(
        queryset=Country.objects.all(),
        default=None,
        style={
            'base_template': 'custom_select.html'
        },
    )
    city = serializers.PrimaryKeyRelatedField(
        queryset=City.objects.all(),
        default=None,
        style={
            'base_template': 'custom_select.html'
        },
    )
    state = serializers.PrimaryKeyRelatedField(
        queryset=Region.objects.all(),
        default=None,
        style={
            'base_template': 'custom_select.html'
        },
    )
    pincode = serializers.CharField(
        max_length=10,
        required=False,
        allow_blank=True,
        allow_null=True,
        style={
            'base_template': 'custom_input.html'
        },
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'country', 'city', 'state', 'pincode','address']
    

    def get_default_country(self):
        # Replace this logic with your desired default selection
        return Country.objects.first()

    def get_default_city(self):
        # Replace this logic with your desired default selection
        return City.objects.first()

    def get_default_state(self):
        # Replace this logic with your desired default selection
        return Region.objects.first()
    
    def validate_last_name(self, value):
        if not re.match(r'^[a-zA-Z]+$', value):
            raise serializers.ValidationError("Last Name can only contain characters.")
        return value
    
    def validate_first_name(self, value):
        if not re.match(r'^[a-zA-Z]+$', value):
            raise serializers.ValidationError("Last Name can only contain characters.")
        return value

    
class ChangePasswordSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = ['password']