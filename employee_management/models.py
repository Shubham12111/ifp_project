from django.db import models

from authentication.models import User

# Create your models here.
class EmployeeUser(User):
    class Meta:
        """
        Meta class for defining additional properties of the model.
        """
        proxy = True
        verbose_name = "Employee"
        verbose_name_plural = "Employees"
        # You can define any additional properties specific to the model here.
        # For example, you can set the default ordering for the model's queryset.
        ordering = ['-id']  # Order by the default primary key in descending order