from rest_framework import serializers
from .models import Contact,ContactType
from cities_light.models import City, Country, Region
from rest_framework.validators import UniqueValidator

class ContactSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(
        max_length=100,
        required= True,
        label='First Name',
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
            'base_template': 'custom_input.html'
        },
    )
    last_name = serializers.CharField(
        max_length=100,
        required= True,
        label='Last Name',
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
            'base_template': 'custom_input.html'
        },
    )
    email = serializers.EmailField(
        label=('Email'),
        max_length=100,
        required= True,
        validators=[UniqueValidator(queryset=Contact.objects.all(), message="Email already exists. Please use a different email.")],
        style={
            "input_type": "email",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
            'base_template': 'custom_input.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Email field is required.",
        },
    )
    phone_number = serializers.CharField(
        label=('Phone'),
        max_length=14,
        required= True,
        style={
            "input_type": "text",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
            "base_template": 'custom_input.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Phone number field is required.",
        },
    )
   

    job_title = serializers.CharField(
        label=('Job Title'),
        max_length=100,
        required= False,
        style={
            "input_type": "text",
            "autofocus": False,
            "autocomplete": "off",
            "base_template": 'custom_input.html'
        }
    )
    company = serializers.CharField(
        label=('Company Name'),
        max_length=100,
        required=False,
        style={
            "input_type": "text",
            "autocomplete": "off",
            "autofocus": False,
            "base_template": 'custom_input.html'
        }
    )
    address = serializers.CharField(
        label=('Address'),
        max_length=100,
        required=False,
        style={
            "input_type": "text",
            "autofocus": False,
            "autocomplete": "off",
            "base_template": 'custom_address.html'
        }
    )
    
    contact_type = serializers.PrimaryKeyRelatedField(
        label=('Contact Type'),
        required=True,
        queryset=ContactType.objects.all(),
        style={
            'base_template': 'custom_required.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Contact Type field cannot be blank.",
            "invalid": "Contact Type can only contain characters.",

        },
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
        label=('Pincode'),
        max_length=6,
        required=False,
        style={
            "input_type": "text",
            "autofocus": False,
            "autocomplete": "off",
            'base_template': 'custom_input.html'
        }
    )

    class Meta:
        model = Contact
        fields = ['contact_type','first_name','last_name', 'email', 'phone_number','company', 'job_title','address','city','state','country','pincode',]

        extra_kwargs={
            'name':{'required':True},
            'email':{'required':True},
            'phone_number':{'required':True},
            'contact_type':{'required':True}

        }

