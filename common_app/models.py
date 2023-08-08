from django.db import models
from django.contrib.auth.models import Group
from ckeditor.fields import RichTextField

PURPOSE_CHOICES = [
        ('new_user_registration', 'New User Registration'),
 ]    
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