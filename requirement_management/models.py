from rest_framework.relations import PrimaryKeyRelatedField
from django.db import models
from authentication.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from ckeditor.fields import RichTextField
from stock_management.models import Category
from customer_management.models import SiteAddress


REQUIREMENT_DEFECT_CHOICES = (
    ('actual_defect', 'Actual Defect'),
    ('recommended', 'Recommended Defect'),
)

REQUIREMENT_CHOICES = (
    ('active', 'Active'),
    ('to-surveyor', 'To Surveyor'),
    ('assigned-to-surveyor ', 'Assigned To Surveyor')
)

REQUIREMENT_DEFECT_STATUS_CHOICES = (
    ('pending', 'Pending'),
    ('in-progress', 'In Progress'),
    ('executed', 'Executed')
)

STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('submit', 'submitted'),
    )

CATEGORY_STATUS_CHOICES = (
        ('active', 'Active'),
        ('in-active', 'Inactive'),
)

# Define the choices for the status field
QUOTATION_STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('submitted', 'Submitted'),
    ('accepted', 'Accepted'),
    ('rejected', 'Rejected'),
]


class Requirement(models.Model):
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
    requirement_id = models.ForeignKey(Requirement, on_delete=models.CASCADE)
    document_path = models.CharField(max_length=256)
    create_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('FRA Action Document')
        verbose_name_plural = _('FRA Action Document')
        
class RequirementDefect(models.Model):
    requirement_id = models.ForeignKey(Requirement, on_delete=models.CASCADE)
    action = models.TextField()
    description = models.TextField()
    reference_number = models.CharField(max_length=50, null=True)
    rectification_description = models.TextField()
    status = models.CharField(max_length=30, choices=REQUIREMENT_DEFECT_STATUS_CHOICES, default='pending')
    defect_type = models.CharField(max_length=30, choices=REQUIREMENT_DEFECT_CHOICES, default='actual_defect')
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


class Report(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='report_user', null=True)
    requirement_id = models.ForeignKey(Requirement, on_delete=models.CASCADE)
    defect_id = models.ManyToManyField(RequirementDefect, blank=True)
    signature_path = models.CharField(max_length=500,null=True)
    pdf_path = models.CharField(max_length=500,null=True)
    comments = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class SORCategory(models.Model):
    """
        Represents a category for Service Order Requests (SOR).

        Attributes:
            user_id (ForeignKey): The user who created this category.
            name (str): The name of the category (limited to 50 characters).
            description (RichTextField, optional): Description of the category (Rich Text Field).
            image_path (str): Path to the category's image (limited to 255 characters).
            status (str): The status of the category (active or inactive).
            created_at (DateTime): Date and time when the category was created (auto-generated).
            updated_at (DateTime): Date and time when the category was last updated (auto-generated).
    """
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sorcategory_user')
    name = models.CharField(max_length=50)
    description = RichTextField(null=True)
    image_path = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=50, choices=CATEGORY_STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        """
        Returns a string representation of the category, which is its name.
        """
        return self.name

class SORItem(models.Model):
    """
        Represents an item related to SOR (Service Order Request).

        Attributes:
            user_id (ForeignKey): The user who created this item.
            customer_id (ForeignKey): The customer who owns this item.
            category_id (ForeignKey): The category to which this item belongs.
            name (str): The name of the item (limited to 50 characters).
            description (RichTextField, optional): Description of the item (Rich Text Field).
            price (Decimal): The price of the item (up to 10 digits with 2 decimal places).
            reference_number (str): A reference number for the item (limited to 50 characters).
            created_at (DateTime): Date and time when the item was created (auto-generated).
            updated_at (DateTime): Date and time when the item was last updated (auto-generated).
    
    """
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, 
                                verbose_name="Created By", related_name="sor_user", null=True)
    
    customer_id = models.ForeignKey(User, on_delete=models.CASCADE)
    category_id = models.ForeignKey(SORCategory, on_delete=models.CASCADE)
    name = models.CharField(max_length=225)
    description =  RichTextField(null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    reference_number = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        """
            Returns a string representation of the item, which is its name.
        """
        return self.name

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id.id,
            'customer_id': self.customer_id.id,
            'category_id': self.category_id.name,
            'name': self.name,
            'price': str(self.price),
            'reference_number': self.reference_number
        }

class SORItemImage(models.Model):
    sor_id = models.ForeignKey(SORItem, on_delete=models.CASCADE, null=True)
    image_path = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Image for {self.sor_id.name}"




class Quotation(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, 
                                verbose_name="Created By", related_name="created_quotations", null=True)
    
    customer_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name="customer_quotations")
    requirement_id = models.ForeignKey(Requirement, on_delete=models.CASCADE, related_name="quotations")
    report_id = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="quotations")
    quotation_json = models.JSONField()  # This field stores JSON data
    
    status = models.CharField(max_length=30, choices=QUOTATION_STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    