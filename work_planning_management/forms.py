import uuid
from typing import Any

from django import forms
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.files.base import ContentFile

from infinity_fire_solutions.aws_helper import upload_file_to_s3, fetch_file_from_s3, delete_file_from_s3

from authentication.models import User

from work_planning_management.models import SitePack
from work_planning_management.serializers import CustomFileValidator


class SitePackAdminForm(forms.ModelForm):
    document_path = forms.FileField(
        label='Upload Document',
        validators=[CustomFileValidator()],
        required=True,
        widget=forms.ClearableFileInput(),
        initial = False
    )

    user_id = forms.ModelChoiceField(
        widget=forms.HiddenInput(),
        queryset=User.objects.all(),
        required=False
    )

    class Meta:
        model = SitePack
        fields = ['name', 'document_path', 'user_id']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize the document_path field with the existing file
        instance = kwargs.get('instance')
        if instance and instance.document_path:
            # Fetch the file from S3 and initialize the file field
            file_content = fetch_file_from_s3(f'{instance.document_path}', f'sitepack_doc')
            file_content = file_content.read()
            self.initial['document_path'] = ContentFile(file_content, name=instance.document_path)
    
    def clean_user_id(self):
        user = self._meta.formfield_callback.keywords.get('request').user._wrapped
        return user
    
    def clean_document_path(self):
        document:InMemoryUploadedFile = self.cleaned_data.get('document_path', None)
        if not document:
            raise forms.ValidationError(
                'this field is required.'
            )
        document.name = f"{str(uuid.uuid4())}_{document.name}"
        return document

    def save(self, commit: bool = False) -> Any:

        previous_file = ''

        if hasattr(self, 'instance'):
            previous_file = self.instance.document_path or ''

        # get the document from the cleaned data and generate a unique name for the document
        document:InMemoryUploadedFile = self.cleaned_data.get('document_path', None)
        try:
            # upload the document to the s3
            upload_file_to_s3(document.name, document, f'sitepack_doc')
            self.cleaned_data['document_path'] = f'/sitepack_doc/{document.name}'
            if previous_file:
                deleted = delete_file_from_s3(previous_file, f'sitepack_doc')
            return super().save(commit)
        
        except Exception as e:
            raise e