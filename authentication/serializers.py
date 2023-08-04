from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework.renderers import HTMLFormRenderer
from django.contrib.auth import update_session_auth_hash
from infinity_fire_solutions.custom_form_validation import *
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


class LoginSerializer(serializers.ModelSerializer):
    """
    Serializer class for user login.
    """

    email = serializers.EmailField(
        label=('Email'),
        required=True,
        max_length=100,
        style={
            "input_type": "email",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
            'base_template': 'custom_fullwidth_input.html'
            
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Email is required.",
        },
    )
    password = serializers.CharField(
        label=('Password '),
        required=True,
        max_length=100,
        style={
            "input_type": "password",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
            'base_template': 'custom_full_width_password.html'
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
    
    last_name = serializers.CharField(
        label=('Last Name '),
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
            "blank": "Last Name is required.",
            "invalid": "Last Name can only contain characters.",
        },
    )
    
    email = serializers.EmailField(
        label=('Email '),
        required=True,
        max_length=100,
        style={
            "input_type": "email",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
            'base_template': 'custom_fullwidth_input.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Email is required.",
        },
    )
    
    password = serializers.CharField(
        label=('Password '),
        required=True,
        max_length=100,
        style={
            "input_type": "password",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
           'base_template': 'custom_password.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Password is required.",
        },
    )
    
    password2 = serializers.CharField(
        label=('Confirm Password '),
        required=True,
        max_length=100,
        style={
            "input_type": "password",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
           'base_template': 'custom_password.html'
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
        label=('Email'),
        required=True,
        max_length=100,
        style={
            "input_type": "email",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
            'base_template': 'custom_fullwidth_input.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Email is required.",
        },
    )

    class Meta:
        fields = ('email')

class ResetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(
        label=('New Password '),
        required=True,
        max_length=100,
        style={
            "input_type": "password",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
            'base_template': 'custom_full_width_password.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Password is required.",
        },
    )
    
    confirm_new_password = serializers.CharField(
        label=('Confirm New Password '),
        required=True,
        max_length=100,
        style={
            "input_type": "password",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
           'base_template': 'custom_full_width_password.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Confirm Password is required.",
        },
        write_only=True
    )
    class Meta:
        model = User
        fields = ('password', 'confirm_new_password')
        
    def validate(self, data):
        custom_validate_password(data.get('password'))
        
        password = data.get('password')
        confirm_password = data.get('confirm_new_password')

        if password and confirm_password and password != confirm_password:
            raise serializers.ValidationError({"confirm_new_password": "Passwords do not match."})

        return data


class UserProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(
        max_length=50,
        label='First Name ',
        required=True,
        error_messages={
            "required": "This field is required.",
            "blank": "First Name is required.",
            "invalid": "Invalid First Name. Only alphabets and spaces are allowed.",
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
        max_length=50,
        label='Last Name ',
        required=True,
        error_messages={
            "required": "This field is required.",
            "blank": "Last Name is required.",
            "invalid": "Invalid Last Name. Only alphabets are allowed.",
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
        min_length=10,
        required=False,
        validators=[validate_phone_number],
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
    town = serializers.PrimaryKeyRelatedField(
        queryset=City.objects.all(),
        default=None,
        style={
            'base_template': 'custom_select.html'
        },
    )
    county = serializers.PrimaryKeyRelatedField(
        queryset=Region.objects.all(),
        default=None,
        style={
            'base_template': 'custom_select.html'
        },
    )
    post_code = serializers.CharField(
        max_length=7,
        required=False,
        allow_blank=True,
        allow_null=True,
        style={
            'base_template': 'custom_input.html'
        },
        validators=[validate_uk_postcode],
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'address' , 'town', 'county', 'country', 'post_code']

    
   
    def validate_first_name(self, value):
        if not re.match(r'^[a-zA-Z\s]+$', value):
            raise serializers.ValidationError("Invalid First Name. Only alphabets and spaces are allowed.")

        if len(value) < 2:
            raise serializers.ValidationError("First Name should be at least 2 characters long.")

        return value

    def validate_last_name(self, value):
        if not re.match(r'^[a-zA-Z\s]+$', value):
            raise serializers.ValidationError("Invalid Last Name. Only alphabets and spaces are allowed.")

        if len(value) < 2:
            raise serializers.ValidationError("Last Name should be at least 2 characters long.")

        return value


    
class ChangePasswordSerializer(serializers.ModelSerializer):
    old_password = serializers.CharField(
        label=('Old Password '),
        required=True,
        max_length=100,
        style={
            "input_type": "password",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
           'base_template': 'custom_full_width_password.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Old Password is required.",
        },
    )
    password = serializers.CharField(
        label=('New Password '),
        required=True,
        max_length=100,
        style={
            "input_type": "password",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
           'base_template': 'custom_full_width_password.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "New Password is required.",
        },
    )
    confirm_password = serializers.CharField(
        label=('Confirm Password '),
        required=True,
        max_length=100,
        style={
            "input_type": "password",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
           'base_template': 'custom_full_width_password.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Confirm Password is required.",
        },
    )

    class Meta:
        model = User
        fields = ['old_password','password', 'confirm_password']

    def validate(self, data):
        user = self.context['request'].user

        if not user.check_password(data['old_password']):
            raise serializers.ValidationError({"old_password":"The old password is incorrect."})
        
        if data['password'] == data['old_password']:
            raise serializers.ValidationError({"password":"The new password cannot be the same as the old password."})

        custom_validate_password(data.get('password'))   

        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password":"The new passwords do not match."})

        return data

    def update(self, instance, validated_data):
        instance.set_password(validated_data['password'])
        instance.save()
        # Update the user's session authentication hash
        update_session_auth_hash(self.context['request'], instance)

        return instance
