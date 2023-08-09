from rest_framework import serializers
from infinity_fire_solutions.custom_form_validation import *
from .models import *


class CategorySerializer(serializers.ModelSerializer):
    file = serializers.FileField(
    label = ('Image'),
    required=False,
    style={
        "input_type": "file",
        "class": "form-control",
        "autofocus": False,
        "autocomplete": "off",
        'base_template': 'custom_file.html',
        'help_text':True,
    },
    ) 
    
    description = serializers.CharField(max_length=1000, 
                                    required=True, 
                                    style={'base_template': 'rich_textarea.html', 'rows': 5},
                                    error_messages={
                                            "required": "This field is required.",
                                            "blank": "Message is required.",
                                        })

    
    class Meta:
        model = Category
        fields = [ 'name', 'description', 'status','file']