from django.db import models
from authentication.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from ckeditor.fields import RichTextField
from django.core.validators import MaxValueValidator
from customer_management.models import SiteAddress

requirement_status = (
    ('pending', 'Pending'),
    ('in-progress', 'In Progress'),
    ('executed', 'Executed')
)


class Requirement(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_requirement')
    customer_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='customer_requirement')
    description = RichTextField()
    UPRN = models.CharField(max_length=12)
    site_address =  models.ForeignKey(SiteAddress, on_delete=models.CASCADE, null=True)
    requirement_date_time = models.DateTimeField()
    quality_surveyor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='surveyor_requirement')
    document_path = models.CharField(max_length=256, null=True, blank=True)
    status = models.CharField(max_length=30,choices = requirement_status, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.customer_id.first_name} {self.customer_id.last_name}'s requirement"


class RequirementDefect(models.Model):
    requirement_id = models.ForeignKey(Requirement, on_delete=models.CASCADE)
    action = models.TextField(max_length=256)
    description = RichTextField()
    defect_period = models.DateTimeField()
    due_date = models.DateTimeField()
    status = models.CharField(max_length=30, choices=requirement_status, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.action


class RequirementDocument(models.Model):
    requirement_id = models.ForeignKey(Requirement, on_delete=models.CASCADE)
    defect_id = models.ForeignKey(RequirementDefect, on_delete=models.CASCADE)
    document_path = models.CharField(max_length=256)
    create_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.requirement_id.id