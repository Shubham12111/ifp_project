from rest_framework import serializers

from .models import Contact,ContactType
from cities_light.models import City, Country, Region


class ContactTypeSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        label=('Contact Type *'),
        max_length=100,
        style={
            "input_type": "text",
            "autofocus": True,
            "autocomplete": "off",
            "required": True,
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Contact type field cannot be blank.",
        },
    )
    class Meta:
        model = ContactType
        fields = '__all__'

class CountrySerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        label=('Country *'),
        max_length=100,
        style={
            "input_type": "text",
            "autofocus": True,
            "autocomplete": "off",
            "required": True,
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Country field cannot be blank.",
        },
    )
    class Meta:
        model = Country
        fields = '__all__'


class CitySerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        label=('City *'),
        max_length=100,
        style={
            "input_type": "text",
            "autofocus": True,
            "autocomplete": "off",
            "required": True,
        },
        error_messages={
            "required": "This field is required.",
            "blank": "City field cannot be blank.",
        },
    )
    class Meta:
        model = Country
        fields = '__all__'


class RegionSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        label=('State *'),
        max_length=100,
        style={
            "input_type": "text",
            "autofocus": True,
            "autocomplete": "off",
            "required": True,
        },
        error_messages={
            "required": "This field is required.",
            "blank": "State field cannot be blank.",
        },
    )
    class Meta:
        model = Region
        fields = '__all__'


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
            "autofocus": True,
            "autocomplete": "off",
            "required": True,
            "autofocus": False,
            'base_template': 'custom_input.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Email field cannot be blank.",
        },
    )
    phone_number = serializers.CharField(
        label=('Phone *'),
        max_length=100,
        style={
            "input_type": "number",
            "autofocus": True,
            "autocomplete": "off",
            "required": True,
            "autofocus": False,
            "base_template": 'custom_input.html'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Phone number field cannot be blank.",
        },
    )
    contact_type = serializers.PrimaryKeyRelatedField(queryset=ContactType.objects.all(), required=True,label=('Contact Type *'))

    job_title = serializers.CharField(
        label=('Job Title'),
        max_length=100,
        required= False,
        style={
            "input_type": "text",
            "autofocus": True,
            "autocomplete": "off",
            "autofocus": False
        }
    )
    company = serializers.CharField(
        label=('Company'),
        max_length=100,
        required=False,
        style={
            "input_type": "text",
            "autofocus": True,
            "autocomplete": "off",
            "autofocus": False
        }
    )
    address = serializers.CharField(
        label=('Address'),
        max_length=100,
        required=False,
        style={
            "input_type": "text",
            "autofocus": True,
            "autocomplete": "off",
            "autofocus": False
        }
    )
    country = serializers.PrimaryKeyRelatedField(queryset=Country.objects.all(), required=False)
    city = serializers.PrimaryKeyRelatedField(queryset=City.objects.all(), required=False)
    state = serializers.PrimaryKeyRelatedField(queryset=Region.objects.all(), required=False)

    
    pincode = serializers.CharField(
        label=('Pincode'),
        max_length=100,
        required=False,
        style={
            "input_type": "text",
            "autofocus": True,
            "autocomplete": "off",
            "autofocus": False
        }
    )

    class Meta:
        model = Contact
        fields = ['name', 'email', 'phone_number', 'contact_type','job_title','company','address','country','city','state','pincode']

        extra_kwargs={
            'name':{'required':True},
            'email':{'required':True},
            'phone_number':{'required':True},
            'contact_type':{'required':True}

        }
