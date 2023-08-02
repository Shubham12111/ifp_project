# todo_app/serializers.py
from rest_framework import serializers
from .models import Todo, Module,Comment, STATUS_CHOICES,PRIORITY_CHOICES
from authentication.models import User
from rest_framework.exceptions import ValidationError
from datetime import date

class TodoListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Todo
        fields = ('id','module', 'assigned_to', 'title', 'description','priority', 'start_date', 'end_date', )
    
class TodoAddSerializer(serializers.ModelSerializer):
    module = serializers.PrimaryKeyRelatedField(
        label=('Module'),
        required=True,
        queryset=Module.objects.all(),
        style={
            'base_template': 'custom_select.html',
            'custom_class':'col-6'
        },
    )
     # Custom CharField for the message with more rows (e.g., 5 rows)
    description = serializers.CharField(max_length=1000, 
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
    
    assigned_to = serializers.PrimaryKeyRelatedField(
        label=('Assigned To'),
        required=True,
        queryset=User.objects.none(),
        style={
            'base_template': 'custom_select.html',
            'custom_class':'col-6'
        },
    )
    
    
    priority = serializers.ChoiceField(
        label='Priority',
        choices=PRIORITY_CHOICES,
        required=True,
        style={
            'base_template': 'custom_select.html',
            'custom_class': 'col-4'
        },
    )
    start_date = serializers.DateField(
        label='Start Date',
        required=True,
        style={
            'base_template': 'custom_datepicker.html',
            'custom_class': 'col-4'
        },
        # Add any additional styles or validators if needed
    )
    end_date = serializers.DateField(
        label='End Date',
        required=True,
        style={
            'base_template': 'custom_datepicker.html',
            'custom_class': 'col-4'
        },
        # Add any additional styles or validators if needed
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = self.context['request'].user
        if user.is_authenticated:
            self.fields['assigned_to'].queryset = User.objects.filter(is_active=True).exclude(pk=user.pk)


    def validate(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if start_date and end_date and start_date > end_date:
            raise ValidationError({'end_date':'End date should be greater than the start date.'})

        return data
    
    # def validate_start_date(self, value):
    #     """
    #     Check that the start_date is not less than the current date.
    #     """
    #     if value < date.today():
    #         raise serializers.ValidationError("Start date cannot be in the past.")
    #     return value

    def validate_description(self, value):
        # Custom validation for the message field to treat <p><br></p> as blank
        is_blank_html = value.strip() == "<p><br></p>"
        
        if is_blank_html:
            raise serializers.ValidationError("Description field is required.")
        return value
    
    class Meta:
        model = Todo
        fields = ('module', 'assigned_to', 'title', 'description','priority', 'start_date', 'end_date', )



class CommentSerializer(serializers.ModelSerializer):
   
    # Custom CharField for the message with more rows (e.g., 5 rows)
    comment = serializers.CharField(max_length=1000, 
                                    required=True, 
                                    style={'base_template': 'rich_textarea.html', 'rows': 5},
                                    error_messages={
                                            "required": "This field is required.",
                                            "blank": "Message is required.",
                                        })

    
    status = serializers.ChoiceField(
        label='Priority',
        choices= (
        ('in-progress', 'In Progress'),
        ('completed', 'Completed')
    ),
        required=True,
        style={
            'base_template': 'custom_select.html',
            'custom_class': 'col-12'
        },
    )

    class Meta:
        model = Comment
        fields = ['comment', 'status']
    
    def validate_comment(self, value):
        # Custom validation for the message field to treat <p><br></p> as blank
        is_blank_html = value.strip() == "<p><br></p>"
        
        if is_blank_html:
            raise serializers.ValidationError("Comment field is required.")
        return value