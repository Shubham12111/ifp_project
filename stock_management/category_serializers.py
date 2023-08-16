import uuid
from django.db import transaction
from rest_framework import serializers
from infinity_fire_solutions.custom_form_validation import *
from infinity_fire_solutions.aws_helper import *
from .models import *


class CategorySerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        label=('Name '),
        required=True,
        max_length=100,
        style={
            "input_type": "text",
            "autofocus": False,
            "autocomplete": "off",
            "required": True,
            'base_template': 'custom_fullwidth_input.html',
        },
        error_messages={
            "required": "This field is required.",
            "blank": "Name is required.",
            "invalid": "Name can only contain characters.",
        },
    )

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
        'custom_class': 'col-6'
    },) 
    
    description = serializers.CharField(max_length=1000, 
                                    required=True, 
                                    style={'base_template': 'rich_textarea.html', 'rows': 5},
                                    error_messages={
                                            "required": "This field is required.",
                                            "blank": "Description is required.",
                                        })

    status = serializers.ChoiceField(
        label='Status',
        choices=CATEGORY_STATUS_CHOICES,
        required=True,
        style={
            'base_template': 'custom_select.html',
            'custom_class': 'col-6'
        },
    )
    class Meta:
        model = Category
        fields = [ 'name', 'description', 'file','status']

    def create(self, validated_data):
        # Pop the 'file' field from validated_data
        file_obj = validated_data.pop('file', None)

        # Create a new instance of Conversation with 'title' and 'message'
        instance = Category.objects.create(**validated_data)
        if file_obj:
            # Generate a unique filename
            unique_filename = f"{str(uuid.uuid4())}_{file_obj.name}"
            upload_file_to_s3(unique_filename, file_obj, f'stock/category/{instance.id}')
            instance.image_path = f'stock/category/{instance.id}/{unique_filename}'
            instance.save()
        return instance
    
    def update(self, instance, validated_data):
        file_obj = validated_data.pop('file', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        with transaction.atomic():
            instance.save()

        # Update associated documents if file_list is provided
        if file_obj:
            # If there was an existing image_path, delete the old file from S3
            if instance.image_path:
                s3_client.delete_object(Bucket=settings.AWS_BUCKET_NAME, Key=instance.image_path)
            unique_filename = f"{str(uuid.uuid4())}_{file_obj.name}"
            upload_file_to_s3(unique_filename, file_obj, f'stock/category/{instance.id}')
            instance.image_path = f'stock/category/{instance.id}/{unique_filename}'
            instance.save()
                    
        
        return instance


    def to_representation(self, instance):
        """
        Serialize the category instance.
        """
        representation = super().to_representation(instance)

        if instance.image_path:
            presigned_url = generate_presigned_url(instance.image_path)
            representation['presigned_url'] = presigned_url
            representation['filename'] = instance.image_path.split('/')[-1]

        if instance.id:
            representation['id'] = instance.id
        return representation