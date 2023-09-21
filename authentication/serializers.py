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
    """
    Custom password validation function.

    Validates the provided password against the following criteria:
    1. Should not contain the word "password."
    2. Should be at least 8 characters long.
    3. Must contain at least 1 digit.
    4. Must contain at least 1 uppercase letter.
    5. Should contain a symbol.
    6. Must contain at least 1 lowercase letter (a-z).

    Args:
        value (str): The password to be validated.

    Returns:
        str: The validated password.

    Raises:
        serializers.ValidationError: If the password does not meet the criteria.
    """
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
    """
    Serializer for user registration (signup).

    This serializer is used to validate and serialize user registration data, including
    first name, last name, email, password, and password confirmation.

    Attributes:
        first_name (serializers.CharField): A field for the user's first name.
        last_name (serializers.CharField): A field for the user's last name.
        email (serializers.EmailField): A field for the user's email address.
        password (serializers.CharField): A field for the user's chosen password.
        password2 (serializers.CharField): A field for confirming the user's password.

    Meta:
        model (User): The User model for which this serializer is defined.
        fields (tuple): The fields to include in the serialized representation.
    """

    first_name = serializers.CharField(
        label=('First Name '),
        required=True,
        max_length=50,
        style={
            "input_type": "text",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
            'base_template': 'custom_fullwidth_input.html'
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
        max_length=50,
        style={
            "input_type": "text",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
            'base_template': 'custom_fullwidth_input.html'
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
           'base_template': 'custom_full_width_password.html'
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
        fields = ('first_name', 'last_name', 'email', 'password', 'password2')
        
    def validate(self, data):
        """
        Custom validation method for validating user registration data.

        Args:
            data (dict): The input data containing user registration information.

        Returns:
            dict: The validated data if successful.

        Raises:
            serializers.ValidationError: If validation fails.
        """
        custom_validate_password(data.get('password'))
        
        password = data.get('password')
        confirm_password = data.get('password2')

        if password and confirm_password and password != confirm_password:
            raise serializers.ValidationError({"password2": "Passwords do not match."})

        return data
    
    def validate_last_name(self, value):
        """
        Custom validation method for last name.

        Args:
            value (str): The last name to be validated.

        Returns:
            str: The validated last name if successful.

        Raises:
            serializers.ValidationError: If validation fails.
        """
        if not re.match(r'^[a-zA-Z]+$', value):
            raise serializers.ValidationError("Last Name can only contain characters.")
        return value
    
    def validate_first_name(self, value):
        """
        Custom validation method for first name.

        Args:
            value (str): The first name to be validated.

        Returns:
            str: The validated first name if successful.

        Raises:
            serializers.ValidationError: If validation fails.
        """
        if not re.match(r'^[a-zA-Z]+$', value):
            raise serializers.ValidationError("Last Name can only contain characters.")
        return value


    def validate_email(self, value):
        """
        Custom validation method for email.

        Args:
            value (str): The email address to be validated.

        Returns:
            str: The validated email address if successful.

        Raises:
            serializers.ValidationError: If validation fails.
        """
        # Call the parent's is_valid() method to perform the default validationif 
        if value:
            user_email = User.objects.filter(email=value).exists()
            if user_email:
                raise serializers.ValidationError('User with this email already exists, Please try with differnt email.')
        return value

    def create(self, validate_data):
        """
        Create a new user instance.

        Args:
            validate_data (dict): The validated user registration data.

        Returns:
            User: The newly created user instance.
        """
        validate_data.pop('password2')
        return User.objects.create_user(**validate_data)

class ForgotPasswordSerializer(serializers.Serializer):
    """
    Serializer for handling password reset requests.

    Attributes:
        email (serializers.EmailField): The email address of the user requesting a password reset.
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

    class Meta:
        fields = ('email')

class ResetPasswordSerializer(serializers.Serializer):
    """
    Serializer for resetting the user's password.

    Attributes:
        password (serializers.CharField): The new password for the user.
        confirm_new_password (serializers.CharField): Confirmation of the new password.
    """
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
        """
        Validate the new password and its confirmation.

        Args:
            data (dict): Dictionary containing the password and confirm_new_password fields.

        Returns:
            dict: Validated data.

        Raises:
            serializers.ValidationError: If the passwords do not match or do not meet password criteria.
        """
        custom_validate_password(data.get('password'))
        
        password = data.get('password')
        confirm_password = data.get('confirm_new_password')

        if password and confirm_password and password != confirm_password:
            raise serializers.ValidationError({"confirm_new_password": "Passwords do not match."})

        return data


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile information.
    """
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
        label='Phone Number',
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
        """
        Validate the first name field.

        Args:
            value (str): First name value.

        Returns:
            str: Validated first name.

        Raises:
            serializers.ValidationError: If the first name is invalid.
        """
        if not re.match(r'^[a-zA-Z\s]+$', value):
            raise serializers.ValidationError("Invalid First Name. Only alphabets and spaces are allowed.")

        if len(value) < 2:
            raise serializers.ValidationError("First Name should be at least 2 characters long.")

        return value

    def validate_last_name(self, value):
        """
        Validate the last name field.

        Args:
            value (str): Last name value.

        Returns:
            str: Validated last name.

        Raises:
            serializers.ValidationError: If the last name is invalid.
        """
        if not re.match(r'^[a-zA-Z\s]+$', value):
            raise serializers.ValidationError("Invalid Last Name. Only alphabets and spaces are allowed.")

        if len(value) < 2:
            raise serializers.ValidationError("Last Name should be at least 2 characters long.")

        return value
    
    def validate_address(self, value):
        """
        Validate the address field.

        Args:
            value (str): Address value.

        Returns:
            str: Validated address.

        Raises:
            serializers.ValidationError: If the address is invalid.
        """
        # Check if address contains only spaces.
        if self.initial_data['address'].isspace():
            raise serializers.ValidationError("Invalid Address. Address can not contain only spaces.")
        
        # Remove morethan one spaces between words in complete addresss like 'phase  one    chandigarh' to 'phase one chandigarh'
        value = re.sub(r'\s+', ' ', value)

        return value
    
    def validate_post_code(self, value):
        """
        Validate the post code field.

        Args:
            value (str): Post code value.

        Returns:
            str: Validated post code.

        Raises:
            serializers.ValidationError: If the post code is invalid.
        """
        # Check if post code contains only spaces.
        if self.initial_data['post_code'].isspace():
            raise serializers.ValidationError("Invalid Post code. Post code can not contain only spaces.")
        
        return value

    
class ChangePasswordSerializer(serializers.ModelSerializer):
    """
    Serializer for changing the user's password.
    """
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
        """
        Validate the password change request.

        Args:
            data (dict): The data to be validated.

        Returns:
            dict: Validated data.

        Raises:
            serializers.ValidationError: If the data is invalid.
        """
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
        """
        Update the user's password.

        Args:
            instance: The user instance.
            validated_data (dict): Validated data.

        Returns:
            instance: The updated user instance.

        Raises:
            serializers.ValidationError: If the data is invalid.
        """
        instance.set_password(validated_data['password'])
        instance.save()
        # Update the user's session authentication hash
        update_session_auth_hash(self.context['request'], instance)

        return instance
