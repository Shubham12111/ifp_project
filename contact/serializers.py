from rest_framework import serializers
from .models import Contact,ContactType
from cities_light.models import City, Country, Region

class ContactSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        label=('Name *'),
        max_length=100,
        style={
            "input_type": "text",
            "autofocus": True,
            "autocomplete": "off",
            "required": True,
            "autofocus": False,
            'base_template': 'custom_input.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Name field cannot be blank.",
            "invalid": "Name can only contain characters.",

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
            'base_template': 'custom_input.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Email field cannot be blank.",
        },
    )
    phone_number = serializers.CharField(
        label=('Phone *'),
        max_length=14,
        style={
            "input_type": "text",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
            "base_template": 'custom_input.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Phone number field cannot be blank.",
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
        }
    )
    
    contact_type = serializers.PrimaryKeyRelatedField(
        label=('Contact Type *'),
        required=True,
        queryset=ContactType.objects.all(),
        style={
            'base_template': 'custom_select.html'
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
        fields = ['contact_type','name', 'email', 'phone_number','job_title','company','country','city','state','pincode','address']

        extra_kwargs={
            'name':{'required':True},
            'email':{'required':True},
            'phone_number':{'required':True},
            'contact_type':{'required':True}

        }

