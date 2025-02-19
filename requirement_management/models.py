from rest_framework.relations import PrimaryKeyRelatedField
from django.db import models
from authentication.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from ckeditor.fields import RichTextField
from stock_management.models import Category
from customer_management.models import SiteAddress
from django.utils import timezone
from datetime import datetime,time




REQUIREMENT_DEFECT_CHOICES = (
    ('actual_defect', 'Actual Defect'),
    ('recommended', 'Recommended Defect'),
)

REQUIREMENT_CHOICES = (
    ('to-survey', 'To Survey'),
    ('assigned-to-surveyor', 'Assigned To Surveyor'),
    ('surveyed', 'Surveyed')
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
    ('quoted', 'Quoted'),
    ('awaiting-approval', 'Awaiting Approval'),
    ('to-commence', 'To Commence'),
    ('rejected', 'Rejected'),
]


# Choices for Unit
UNIT_CHOICES = (
    ('no', 'No'),
    ('week', 'Week'),
    ('sqm', 'SqM'),
    ('lm', 'LM'),
    ('unit', 'Unit'),
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
    description = RichTextField()
    action = RichTextField()
    site_address =  models.ForeignKey(SiteAddress, on_delete=models.CASCADE, null=True)
    due_date = models.DateField(null=True, blank=True)
    survey_start_date = models.DateTimeField(null=True, blank=True)
    survey_end_date = models.DateTimeField(null=True, blank=True)
    quantity_surveyor = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name='surveyor_requirement')
    surveyor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='surveyor', null=True, blank=False)
    status = models.CharField(max_length=30,choices = REQUIREMENT_CHOICES, default='to-survey')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('FRA Action')
        verbose_name_plural = _('FRA Action')
        ordering = ['-id']  # Order by the default primary key in descending order

    def __str__(self):
        return f"{self.customer_id.first_name} {self.customer_id.last_name}'s requirement"
    

    def update_created_at(self, date_str):
        """
        Update the 'created_at' field with a new date.
        """
        if date_str:
            try:
                if isinstance(date_str, str):
                    # If date_str is a string (e.g., from a CSV file), parse it into a datetime object
                    date = datetime.strptime(date_str, '%Y-%m-%d').date()
                elif isinstance(date_str, datetime):
                    # If date_str is a datetime object (e.g., from an Excel file), use it directly
                    date = date_str.date()
                else:
                    raise ValueError("Invalid date_str format")
            
                # Set the 'created_at' field
                self.created_at = timezone.make_aware(datetime.combine(date, time.min))
                self.save()
            except ValueError as e:
                # Handle any parsing errors or invalid date formats here
                print(f"Error parsing date string: {e}")

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
    action = RichTextField()
    description = RichTextField()
    reference_number = models.CharField(max_length=50, null=True)
    rectification_description = RichTextField()
    status = models.CharField(max_length=30, choices=REQUIREMENT_DEFECT_STATUS_CHOICES, default='pending')
    defect_type = models.CharField(max_length=30, choices=REQUIREMENT_DEFECT_CHOICES, default='actual_defect')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.action
    class Meta:
        verbose_name = _('Fire Risk Assessment Defect')
        verbose_name_plural = _('Fire Risk Assessment Defect')
        ordering = ['-id']  # Order by the default primary key in descending order

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
        comments (RichTextField): Comments for the report.
        status (CharField): Status of the report (choices defined in STATUS_CHOICES).
        created_at (DateTimeField): Date and time when the report was created.
        updated_at (DateTimeField): Date and time when the report was last updated.
    """
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='report_user', null=True)
    requirement_id = models.ForeignKey(Requirement, on_delete=models.CASCADE)
    defect_id = models.ManyToManyField(RequirementDefect, blank=True)
    signature_path = models.CharField(max_length=500,null=True)
    pdf_path = models.CharField(max_length=500,null=True)
    comments = RichTextField(blank=True, null=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-id']  # Order by the default primary key in descending order

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
    
    class Meta:
        verbose_name = _('SOR Category')
        verbose_name_plural = _('SOR Category')

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
    
    customer_id = models.ForeignKey(User, on_delete=models.CASCADE,null=True)
    category_id = models.ForeignKey(SORCategory, on_delete=models.CASCADE)
    name = models.CharField(max_length=225)
    description =  RichTextField(null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    reference_number = models.CharField(max_length=50)
    units = models.CharField(max_length=20, choices=UNIT_CHOICES, default='no')
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
            'user_id': self.user_id.id if self.user_id else '',
            'customer_id': self.customer_id.id if self.customer_id else '',
            'category_id': self.category_id.name,
            'name': self.name,
            'price': str(self.price),
            'description':self.description,
            'reference_number': self.reference_number,
            'units':self.units
        }
    
class SORItemProxy(SORItem):

    """
    Proxy model representing a default version of an item related to SOR (Service Order Request).

    This model inherits from the SORItem model and serves as a proxy, allowing customization
    and extensions without creating a separate database table.

    Attributes:
        Inherits attributes from the SORItem model.
    """
    
    class Meta:
        """
    Meta:
        proxy (bool): Indicates that this is a proxy model.
        verbose_name (str): Human-readable name for a single object of this model.
        verbose_name_plural (str): Human-readable name for the plural of this model.
    """
        proxy = True
        verbose_name = 'SOR Item'
        verbose_name_plural = 'SOR Items'

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
    defect_id = models.ManyToManyField(RequirementDefect, blank=True)
    quotation_json = models.JSONField()  # This field stores JSON data
    total_amount = models.DecimalField(max_digits=10, decimal_places=2,null=True, blank=True)
    status = models.CharField(max_length=30, choices=QUOTATION_STATUS_CHOICES, default='draft')
    submitted_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    pdf_path = models.CharField(max_length=500,null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering =['id']
    