# todo_app/serializers.py
from bs4 import BeautifulSoup
from rest_framework import serializers
from .models import Todo, Module,Comment, STATUS_CHOICES,PRIORITY_CHOICES
from authentication.models import User
from rest_framework.exceptions import ValidationError
from datetime import date

def get_html_text(html_content):
    """
    Summary:
        Fetches HTML content from a given URL and extracts the text enclosed in HTML tags.
    Arguments:
        url (str): The URL of the webpage to fetch.
    Returns:
        html_text (str): The text content enclosed in HTML tags.
    """
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract text enclosed in HTML tags
    html_text = soup.get_text()
    
    return html_text

class TodoListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Todo
        fields = ('id', 'user_id', 'module', 'assigned_to', 'title', 'description','priority', 'status', 'start_date', 'end_date')
    
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        
        ret['user_id'] = f"{instance.user_id.first_name} {instance.user_id.last_name}"
        ret['assigned_to'] = f"{instance.assigned_to.first_name} {instance.assigned_to.last_name} - <i>{instance.assigned_to.roles}</i>"
        ret['module'] = f'{instance.module.name}'
        ret['priority'] = f'{instance.get_priority_display()}'
        ret['status'] = f'{instance.get_status_display()}'
        ret['start_date'] = f"{instance.start_date.strftime('%d/%m/%Y')}"
        ret['end_date'] = f"{instance.end_date.strftime('%d/%m/%Y')}"
        ret['description'] = get_html_text(instance.description)

        return ret 
    
class TodoAddSerializer(serializers.ModelSerializer):
    module = serializers.SlugRelatedField(
        slug_field='name',
        label=('Module'),
        required=True,
        queryset=Module.objects.all(),
        style={
            'base_template': 'custom_search.html',
            'custom_class':'col-6'
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Module field cannot be blank.",
            "invalid": "Module can only contain characters.",
            'does_not_exist': 'Module with {slug_name}, {value} does not exist.',
            'null': "This field is required."
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
            'custom_class':'col-6 autocomplete'
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
        input_formats=['%d/%m/%Y','iso-8601'],
        style={
            'base_template': 'custom_datepicker.html',
            'custom_class': 'col-4'
        },
        # Add any additional styles or validators if needed
    )
    end_date = serializers.DateField(
        label='End Date',
        required=True,
        input_formats=['%d/%m/%Y','iso-8601'],
        style={
            'base_template': 'custom_datepicker.html',
            'custom_class': 'col-4'
        },
        # Add any additional styles or validators if needed
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            user = self.context['request'].user
            if user.is_authenticated:
                self.fields['assigned_to'].queryset = User.objects.filter(is_employee=True, is_active=True).exclude(roles__name='Customer')
        except Exception as e:
            pass

    def validate(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if start_date and end_date and start_date > end_date:
            raise ValidationError({'end_date':'End date should be greater than the start date.'})

        return data
    

    def validate_description(self, value):
        # Custom validation for the message field to treat <p><br></p> as blank
        soup = BeautifulSoup(value, 'html.parser')
        cleaned_comment = soup.get_text().strip()

        # Check if the cleaned comment consists only of whitespace characters
        if not cleaned_comment:
            raise serializers.ValidationError("Description is required.")

        if all(char.isspace() for char in cleaned_comment):
            raise serializers.ValidationError("Description cannot consist of only spaces and tabs.")

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
        label='Status',
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
        soup = BeautifulSoup(value, 'html.parser')
        cleaned_comment = soup.get_text().strip()

        # Check if the cleaned comment consists only of whitespace characters
        if not cleaned_comment:
            raise serializers.ValidationError("Comment is required.")

        if all(char.isspace() for char in cleaned_comment):
            raise serializers.ValidationError("Comment cannot consist of only spaces and tabs.")

        return value