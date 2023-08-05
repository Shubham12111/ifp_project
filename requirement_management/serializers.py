from rest_framework import serializers
from .models import Requirement, requirement_status, RequirementDefect
from django.utils.html import strip_tags
from authentication.models import User
from bs4 import BeautifulSoup
from customer_management.models import SiteAddress


class CustomerNameField(serializers.RelatedField):
    def to_representation(self, value):
        return f"{value.first_name} {value.last_name}"
    

class RequirementDefectSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = RequirementDefect
        fields = ('id', 'requirement_id', 'action', 'description', 'defect_period', 'due_date', 'status')
    

class RequirementDetailSerializer(serializers.ModelSerializer):
    customer_name = CustomerNameField(source='customer_id', read_only=True)
    quality_surveyor_name = CustomerNameField(source='quality_surveyor', read_only=True)
    requirementdefect_set = RequirementDefectSerializer(many=True, read_only=True)
    class Meta:
        model = Requirement
        fields = ('user_id', 'customer_id', 'description', 'UPRN', 'requirement_date_time', 'quality_surveyor', 'status', 'customer_name', 'quality_surveyor_name', 'requirementdefect_set')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['description'] = strip_tags(data['description']) # to strip html tags attached to response by ckeditor RichText field.
        return data

class RequirementSerializer(serializers.ModelSerializer):

    class Meta:
        model = Requirement
        fields = ('user_id', 'customer_id', 'description', 'UPRN', 'requirement_date_time', 'quality_surveyor', 'status')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['description'] = strip_tags(data['description']) # to strip html tags attached to response by ckeditor RichText field.
        return data
    


class RequirementAddSerializer(serializers.ModelSerializer):
    customer_id = serializers.PrimaryKeyRelatedField(
        label=('Customer'),
        required=True,
        queryset=User.objects.filter(roles__name='Customer'),
        style={
            'base_template': 'custom_customer_select.html',
            'custom_class':'col-12'
        },
    )
    description = serializers.CharField(
        max_length=1024, 
        required=True, 
        style={'base_template': 'rich_textarea.html'},
        error_messages={
            "required": "This field is required.",
            "blank": "description is required.",
        }
    )
    UPRN = serializers.CharField(
    max_length=12, 
    label=('UPRN'),
    required=False,  # Make it optional
    style={
        "input_type": "number",  # Use "number" input type
        "min": 0,  # Optional: Set minimum value if needed
        "max": 999999999999,  # Optional: Set maximum value if needed
        "autocomplete": "off",
        "required": False,  # Adjust as needed
        'base_template': 'custom_input.html',
        'custom_class': 'col-6'
    },
    error_messages={
            "blank": "UPRN Name is required.",
            "invalid": "It must contain a 12-digit number.",
        },
    )
    requirement_date_time = serializers.DateTimeField(
        label='Requirement Date Time',
        required=True,
        style={
            'base_template': 'custom_date_time.html',
            'custom_class': 'col-6'
        },
    )
   
    quality_surveyor = serializers.PrimaryKeyRelatedField(
        label=('Quality Surveyor'),
        required=True,
        queryset=User.objects.all(),
        style={
            'base_template': 'custom_select.html',
            'custom_class':'col-6'
        },
    )

    def validate_description(self, value):
        # Custom validation for the message field to treat <p><br></p> as blank
        soup = BeautifulSoup(value, 'html.parser')
        cleaned_comment = soup.get_text().strip()

        if not cleaned_comment:
            raise serializers.ValidationError("Description is required.")
        
        is_blank_html = value.strip() == "<p><br></p>"
        
        if is_blank_html:
            raise serializers.ValidationError("Description field is required.")
        return value
    
    class Meta:
        model = Requirement
        fields = ('customer_id', 'quality_surveyor','description', 'UPRN', 'requirement_date_time')
      

class RequirementDefectAddSerializer(serializers.ModelSerializer):
    
    description = serializers.CharField(
        max_length=1000, 
        required=True, 
        style={'base_template': 'rich_textarea.html'},
        error_messages={
            "required": "This field is required.",
            "blank": "description is required.",
        }
    )

    defect_period = serializers.DateTimeField(
        label='Defect Period',
        required=True,
        style={
            'base_template': 'custom_date_time.html',
            'custom_class': 'col-6'
        },
    )

    due_date = serializers.DateTimeField(
        label='Due Date',
        required=True,
        style={
            'base_template': 'custom_date_time.html',
            'custom_class': 'col-6'
        },
    )

    class Meta:
        model = RequirementDefect
        fields = ('action', 'description', 'defect_period', 'due_date', 'status')