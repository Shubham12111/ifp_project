from django.db import models
from django.contrib.auth.models import Group
from ckeditor.fields import RichTextField
from django.utils import timezone


PURPOSE_CHOICES = [
        ('new_user_registration', 'New User Registration'),
 ]   

class AdminConfiguration(models.Model):
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=20.00)  # Default tax rate of 20%

    def __str__(self):
        return f"Tax Rate: {self.tax_rate}%"


class MenuItem(models.Model):
    permission_required = models.BooleanField(default=False)
    name = models.CharField(max_length=100)
    url = models.CharField(max_length=200)
    icon = models.CharField(max_length=100)
    order = models.IntegerField()
    
    # Self-referencing ForeignKey for sub-menu functionality
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class EmailNotificationTemplate(models.Model):
    purpose = models.CharField(max_length=50, choices=PURPOSE_CHOICES, unique=True)
    subject = models.CharField(max_length=200)
    recipient = models.EmailField()
    content =  RichTextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,null=True)

    
    def __str__(self):
        return self.subject
    

class UpdateWindowConfiguration(models.Model):
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"Update Window ({self.start_date} - {self.end_date})"
    

class SORValidity(models.Model):
    sor_expiration_date = models.DateTimeField(
        verbose_name="Expiration Date",
        help_text="The date and time when this item will expire.",
        blank=True,
        null=True
    )

    update_window = models.ForeignKey(UpdateWindowConfiguration, on_delete=models.CASCADE)

    def is_within_update_window(self):
        now = timezone.now()
        return self.update_window.is_active and self.update_window.start_date <= now <= self.update_window.end_date

    def is_expired(self):
        """
        Check if the item has expired.
        """
        if self.sor_expiration_date and timezone.now() > self.sor_expiration_date:
            return True
        return False

    # def is_within_edit_window(self):
    #     """
    #     Check if the item is within the edit window (e.g., within 10 days after expiration).
    #     """
    #     if self.expiration_date:
    #         edit_window_end_date = self.expiration_date + timezone.timedelta(days=10)
    #         if timezone.now() <= edit_window_end_date:
    #             return True
    #     return False
    


    
    