from django.db import models
from authentication.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from ckeditor.fields import RichTextField
from django.core.validators import MaxValueValidator
from customer_management.models import SiteAddress

REQUIREMENT_CHOICES = (
    ('active', 'Active'),
    ('to-surveyor', 'To Surveyor'),
    ('assigned-to-surveyor ', 'Assigned To Surveyor')
)


REQUIREMENT_DEFECT_CHOICES = (
    ('pending', 'Pending'),
    ('in-progress', 'In Progress'),
    ('executed', 'Executed')
)

STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('submitted', 'submitted'),
    )

class Requirement(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_requirement')
    customer_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='customer_requirement')
    description = models.TextField()
    action = models.TextField()
    site_address =  models.ForeignKey(SiteAddress, on_delete=models.CASCADE, null=True)
    quantity_surveyor = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name='surveyor_requirement')
    surveyor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='surveyor', null=True, blank=False)
    status = models.CharField(max_length=30,choices = REQUIREMENT_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Fire Risk Assessment')
        verbose_name_plural = _('Fire Risk Assessment')

    def __str__(self):
        return f"{self.customer_id.first_name} {self.customer_id.last_name}'s requirement"

class RequirementAsset(models.Model):
    requirement_id = models.ForeignKey(Requirement, on_delete=models.CASCADE)
    document_path = models.CharField(max_length=256)
    create_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Fire Risk Assessment Document')
        verbose_name_plural = _('Fire Risk Assessment Document')
        
class RequirementDefect(models.Model):
    requirement_id = models.ForeignKey(Requirement, on_delete=models.CASCADE)
    UPRN = models.CharField(max_length=12, null=True)
    action = models.TextField(max_length=1000)
    description = RichTextField()
    defect_period = models.DateTimeField()
    due_date = models.DateTimeField()
    reference_number = models.CharField(max_length=50, null=True)
    rectification_description = models.TextField()
    status = models.CharField(max_length=30, choices=REQUIREMENT_DEFECT_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.action
    class Meta:
        verbose_name = _('Fire Risk Assessment Defect')
        verbose_name_plural = _('Fire Risk Assessment Defect')

class RequirementDefectDocument(models.Model):
    requirement_id = models.ForeignKey(Requirement, on_delete=models.CASCADE)
    defect_id = models.ForeignKey(RequirementDefect, on_delete=models.CASCADE)
    document_path = models.CharField(max_length=256)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Fire Risk Assessment Defect Document')
        verbose_name_plural = _('Fire Risk Assessment Defect Document')

