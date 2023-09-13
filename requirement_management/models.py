from rest_framework.relations import PrimaryKeyRelatedField
from django.db import models
from authentication.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from ckeditor.fields import RichTextField
from stock_management.models import Category
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
    """
    Model for storing requirements.

    Attributes:
        user_id (ForeignKey): The user who created the requirement.
        customer_id (ForeignKey): The customer associated with the requirement.
        UPRN (CharField): UPRN (Unique Property Reference Number) for the requirement.
        RBNO (CharField): RBNO (Reference Building Number) for the requirement.
        description (TextField): Description of the requirement.
        action (TextField): Action for the requirement.
        site_address (ForeignKey): The site address associated with the requirement.
        quantity_surveyor (ForeignKey): The quantity surveyor assigned to the requirement.
        surveyor (ForeignKey): The surveyor associated with the requirement.
        status (CharField): Status of the requirement (choices defined in REQUIREMENT_CHOICES).
        created_at (DateTimeField): Date and time when the requirement was created.
        updated_at (DateTimeField): Date and time when the requirement was last updated.
    """
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_requirement')
    customer_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='customer_requirement')
    UPRN = models.CharField(max_length=255, null=True)
    RBNO = models.CharField(max_length=255, null=True)
    description = models.TextField()
    action = models.TextField()
    site_address =  models.ForeignKey(SiteAddress, on_delete=models.CASCADE, null=True)
    quantity_surveyor = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name='surveyor_requirement')
    surveyor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='surveyor', null=True, blank=False)
    status = models.CharField(max_length=30,choices = REQUIREMENT_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('FRA Action')
        verbose_name_plural = _('FRA Action')

    def __str__(self):
        return f"{self.customer_id.first_name} {self.customer_id.last_name}'s requirement"

class RequirementAsset(models.Model):
    """
    Model for storing requirement assets.

    Attributes:
        requirement_id (ForeignKey): The requirement associated with the asset.
        document_path (CharField): Path to the asset document.
        created_at (DateTimeField): Date and time when the asset was created.
        updated_at (DateTimeField): Date and time when the asset was last updated.
    """
    requirement_id = models.ForeignKey(Requirement, on_delete=models.CASCADE)
    document_path = models.CharField(max_length=256)
    create_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('FRA Action Document')
        verbose_name_plural = _('FRA Action Document')
        
class RequirementDefect(models.Model):
    """
    Model for storing requirement defects.

    Attributes:
        requirement_id (ForeignKey): The requirement associated with the defect.
        action (TextField): Action for the defect.
        description (TextField): Description of the defect.
        reference_number (CharField): Reference number for the defect.
        rectification_description (TextField): Description of rectification for the defect.
        status (CharField): Status of the defect (choices defined in REQUIREMENT_DEFECT_CHOICES).
        created_at (DateTimeField): Date and time when the defect was created.
        updated_at (DateTimeField): Date and time when the defect was last updated.
    """
    requirement_id = models.ForeignKey(Requirement, on_delete=models.CASCADE)
    action = models.TextField()
    description = models.TextField()
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
    """
    Model for storing requirement defect documents.

    Attributes:
        requirement_id (ForeignKey): The requirement associated with the defect document.
        defect_id (ForeignKey): The defect associated with the defect document.
        document_path (CharField): Path to the defect document.
        created_at (DateTimeField): Date and time when the defect document was created.
        updated_at (DateTimeField): Date and time when the defect document was last updated.
    """
    requirement_id = models.ForeignKey(Requirement, on_delete=models.CASCADE)
    defect_id = models.ForeignKey(RequirementDefect, on_delete=models.CASCADE)
    document_path = models.CharField(max_length=256)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Fire Risk Assessment Defect Document')
        verbose_name_plural = _('Fire Risk Assessment Defect Document')


class Report(models.Model):
    """
    Model for storing reports.

    Attributes:
        user_id (ForeignKey): The user associated with the report.
        requirement_id (ForeignKey): The requirement associated with the report.
        defect_id (ManyToManyField): The defects associated with the report.
        signature_path (CharField): Path to the report's signature.
        pdf_path (CharField): Path to the report's PDF.
        comments (TextField): Comments for the report.
        status (CharField): Status of the report (choices defined in STATUS_CHOICES).
        created_at (DateTimeField): Date and time when the report was created.
        updated_at (DateTimeField): Date and time when the report was last updated.
    """
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='report_user', null=True)
    requirement_id = models.ForeignKey(Requirement, on_delete=models.CASCADE)
    defect_id = models.ManyToManyField(RequirementDefect, blank=True)
    signature_path = models.CharField(max_length=500,null=True)
    pdf_path = models.CharField(max_length=500,null=True)
    comments = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class SOR(models.Model):
    customer_id = models.ForeignKey(User, on_delete=models.CASCADE)
    category_id = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    description =  RichTextField(null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    reference_number = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class SORImage(models.Model):
    sor_id = models.ForeignKey(SOR, on_delete=models.CASCADE, null=True)
    image_path = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Image for {self.sor_id.name}"