from django.core.validators import FileExtensionValidator
from django.conf import settings
from rest_framework.serializers import ValidationError


class CustomFileValidator(FileExtensionValidator):
    """
    Custom file validator for validating file extensions and size.

    This validator extends the functionality of Django's FileExtensionValidator by also checking
    the file size to ensure it doesn't exceed a maximum allowed size.

    Attributes:
        allowed_extensions (list): The list of allowed file extensions.
    """
    def __init__(self, allowed_extensions=settings.SUPPORTED_EXTENSIONS, *args, **kwargs):
        """
        Initialize the CustomFileValidator.

        Args:
            allowed_extensions (list): The list of allowed file extensions.
        """
        super().__init__(allowed_extensions, *args, **kwargs)

    def __call__(self, value):
        """
        Validate the file's extension and size.

        This method checks both the file extension and size to ensure they meet the specified criteria.

        Args:
            value (File): The uploaded file.

        Raises:
            serializers.ValidationError: If the file extension or size is invalid.
        """
        extension_error = None
        size_error = None

        try:
            super().__call__(value)
        except ValidationError as e:
            extension_error = e.error_list[0].messages[0]

        max_size = 5 * 1024 * 1024  # 5MB in bytes
        if value.size > max_size:
            size_error = "File size must be no more than 5MB."

        if extension_error or size_error:
            errors = {}
            if extension_error:
                errors['extension'] = [extension_error]
            if size_error:
                errors['size'] = [size_error]
            raise ValidationError(errors)

class CustomImageFileValidator(CustomFileValidator):
    def __init__(self, allowed_extensions=settings.IMAGE_SUPPORTED_EXTENSIONS, *args, **kwargs):
        """
        Initialize the CustomFileValidator.

        Args:
            allowed_extensions (list): The list of allowed file extensions.
        """
        super().__init__(allowed_extensions, *args, **kwargs)