from django.core.validators import RegexValidator

from rest_framework import serializers
from .models import Contact,ContactType,Conversation,ConversationType
from cities_light.models import City, Country, Region
from rest_framework.validators import UniqueValidator
from django.conf import settings

class PhoneNumberValidator(RegexValidator):
    regex = r'^\d+$'
    message = 'Phone number must contain only digits.'

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
        validators=[PhoneNumberValidator()]
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
            'base_template': 'custom_select.html',
             'custom_class':'col-12'
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
    county = serializers.PrimaryKeyRelatedField(
        queryset=Region.objects.all(),
        default=None,
        style={
            'base_template': 'custom_select.html'
        },
    )

    
    post_code = serializers.CharField(
        label=('Post Code'),
        max_length=7,
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
        fields = ['contact_type','first_name','last_name', 'email', 'phone_number','company', 'job_title','address','city','county','country','post_code',]

        extra_kwargs={
            'name':{'required':True},
            'email':{'required':True},
            'phone_number':{'required':True},
            'contact_type':{'required':True}

        }


class ConversationSerializer(serializers.ModelSerializer):
    # Custom FileField for handling file uploads
    file = serializers.FileField(
        label=('Document'),
        required=False,
        style={
            "input_type": "file",
            "class":"form-control",
            "autofocus": False,
            "autocomplete": "off",
            'base_template': 'custom_file.html'
        }
    )
    
    # Custom CharField for the message with more rows (e.g., 5 rows)
    message = serializers.CharField(max_length=1000, 
                                    required=True, 
                                    style={'base_template': 'rich_textarea.html', 'rows': 5},
                                    error_messages={
                                            "required": "This field is required.",
                                            "blank": "Message is required.",
                                        })

    
    title = serializers.CharField(
        max_length=250, 
        label=('Title'),
        required=True,
        style={
            "input_type": "input",
            "autofocus": False,
            "autocomplete": "off",
            'base_template': 'custom_fullwidth_input.html',
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Title is required.",
        },
    )
    conversation_type = serializers.PrimaryKeyRelatedField(
        label=('Conversation Type'),
        required=True,
        queryset=ConversationType.objects.all(),
        style=
        {
            'base_template': 'custom_select.html',
            'custom_class': 'col-12'
        },
    )

    class Meta:
        model = Conversation
        fields = [ 'conversation_type', 'title', 'message','file']
    
    def validate_message(self, value):
        # Custom validation for the message field to treat <p><br></p> as blank
        is_blank_html = value.strip() == "<p><br></p>"
        
        if is_blank_html:
            raise serializers.ValidationError("Message field is required.")
        return value
    
    