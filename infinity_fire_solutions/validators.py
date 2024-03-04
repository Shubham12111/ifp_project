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
        super().__call__(value)

        max_size = 5 * 1024 * 1024  # 5MB in bytes
        if value.size > max_size:
            raise ValidationError(
                "File size must be no more than 5MB.",
                'max_size',
            )
            

class CustomImageFileValidator(CustomFileValidator):
    def __init__(self, allowed_extensions=settings.IMAGE_SUPPORTED_EXTENSIONS, *args, **kwargs):
        """
        Initialize the CustomFileValidator.

        Args:
            allowed_extensions (list): The list of allowed file extensions.
        """
        super().__init__(allowed_extensions, *args, **kwargs)