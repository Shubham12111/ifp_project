import os
from typing import Any
from django.core.management.base import BaseCommand
from authentication.models import User

class Command(BaseCommand):

    def handle(self, *args: Any, **options: Any) -> None:

        """
        Creates a superuser if one does not already exist.

        Parameters:
        *args: variable length argument list.
        **options: variable length keyword argument list.

        Returns:
        None.
        """

        # check if a superuser already exist.
        User.objects.create_superuser(os.environ['SU_EMAIL'], os.environ['SU_PASSWORD'])
        if not User.objects.filter(is_superuser=1).exists():
            # This function creates a superuser if one does not already exist.
            User.objects.create_superuser(os.environ['SU_EMAIL'], os.environ['SU_PASSWORD'])
