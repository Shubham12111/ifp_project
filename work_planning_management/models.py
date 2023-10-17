from django.db import models


# Create your models here.

from django.utils.translation import gettext_lazy as _
from requirement_management.models import Quotation  

from authentication.models import User
from customer_management.models import SiteAddress


STW_CHOICES = (
    ('active', 'Active'),
    ('pending', 'Pending'),
    ('completed', 'Completed')
)

STW_DEFECT_STATUS_CHOICES=(
    ('pending', 'Pending'),
    ('in-progress', 'In Progress'),
    ('executed', 'Executed')
)

STW_DEFECT_CHOICES=(
    ('actual_defect', 'Actual Defect'),
    ('recommended', 'Recommended Defect'),
)


RLO_STATUS_CHOICES = (
    ('approved', 'Approved'),
    ('pending', 'Pending'),
    ('rejected', 'Rejected')
)
class STWRequirements(models.Model):
    """
    Model for storing STW.

    Attributes:
        user_id (ForeignKey): The user who created the STW.
        UPRN (CharField): UPRN (Unique Property Reference Number) for the STW.
        RBNO (CharField): RBNO (Reference Building Number) for the STW.
        description (TextField): Description of the STW.
        action (TextField): Action for the STW.
        site_address (ForeignKey): The site address associated with the STW.
        status (CharField): Status of the STW (choices defined in REQUIREMENT_CHOICES).
        created_at (DateTimeField): Date and time when the STW was created.
        updated_at (DateTimeField): Date and time when the STW was last updated.
    """
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stw_user')
    customer_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stw_requirement')
    UPRN = models.CharField(max_length=255, null=True)
    RBNO = models.CharField(max_length=255, null=True)
    description = models.TextField()
    action = models.TextField()
    building_name = models.CharField(max_length=255, null=True)
    postcode = models.CharField(max_length=255)
    site_address =  models.ForeignKey(SiteAddress, on_delete=models.CASCADE, null=True)
    status = models.CharField(max_length=30,choices = STW_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('STW Requirements')
        verbose_name_plural = _('STW Requirements')

    def __str__(self):
        return f"{self.user_id.first_name} {self.user_id.last_name}'s STW Requirement"
    

class STWAsset(models.Model):
    """
    Model for storing STW assets.

    Attributes:
        stw_id (ForeignKey): The stw associated with the asset.
        document_path (CharField): Path to the asset document.
        created_at (DateTimeField): Date and time when the asset was created.
        updated_at (DateTimeField): Date and time when the asset was last updated.
    """
    stw_id = models.ForeignKey(STWRequirements, on_delete=models.CASCADE)
    document_path = models.CharField(max_length=256)
    create_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('STW Action Document')
        verbose_name_plural = _('STW Action Document')
        
class STWDefect(models.Model):
    """
    Model for storing STW defects.

    Attributes:
        stw_id (ForeignKey): The STW associated with the defect.
        action (TextField): Action for the defect.
        description (TextField): Description of the defect.
        reference_number (CharField): Reference number for the defect.
        rectification_description (TextField): Description of rectification for the defect.
        status (CharField): Status of the defect (choices defined in STW_DEFECT_CHOICES).
        created_at (DateTimeField): Date and time when the defect was created.
        updated_at (DateTimeField): Date and time when the defect was last updated.
    """
    stw_id = models.ForeignKey(STWRequirements, on_delete=models.CASCADE)
    action = models.TextField()
    description = models.TextField()
    reference_number = models.CharField(max_length=50, null=True)
    rectification_description = models.TextField()
    status = models.CharField(max_length=30, choices=STW_DEFECT_STATUS_CHOICES, default='pending')
    defect_type = models.CharField(max_length=30, choices=STW_DEFECT_CHOICES, default='actual_defect')
    # JSONField to store SOR-related data
    sor_data = models.JSONField(null=True, blank=True)  # You can adjust null and blank based on your needs
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.action
    class Meta:
        verbose_name = _('STW Defect')
        verbose_name_plural = _('STW Defect')

class STWDefectDocument(models.Model):
    """
    Model for storing STW defect documents.

    Attributes:
        stw_id (ForeignKey): The STW associated with the defect document.
        defect_id (ForeignKey): The defect associated with the defect document.
        document_path (CharField): Path to the defect document.
        created_at (DateTimeField): Date and time when the defect document was created.
        updated_at (DateTimeField): Date and time when the defect document was last updated.
    """
    stw_id = models.ForeignKey(STWRequirements, on_delete=models.CASCADE)
    defect_id = models.ForeignKey(STWDefect, on_delete=models.CASCADE)
    document_path = models.CharField(max_length=256)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('STW Defect Document')
        verbose_name_plural = _('STW Defect Document')
    

class Job(models.Model):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE)  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f" Job {self.id} for {self.quotation.id}"
    
class RLOLetterTemplate(models.Model):
    name = models.CharField(max_length=100, null=True)
    site_address_info = models.TextField(null=True)
    company_info = models.TextField(null=True)
    main_content_block = models.TextField(null=True)
    complete_template = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('RLO Letter Template')
        verbose_name_plural = _('RLO Letter Templates')

    def __str__(self):
        return self.name

class RLO(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rlo_user')
    name = models.CharField(max_length=100, null=True)
    status = models.CharField(max_length=30, choices=RLO_STATUS_CHOICES, default='pending')
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    base_template = models.ForeignKey(RLOLetterTemplate, on_delete=models.CASCADE, null=True)
    edited_content =  models.TextField(blank=True, null=True)  # New field to store edited template content 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('RLO')
        verbose_name_plural = _('RLO')

    def __str__(self):
        return self.name
