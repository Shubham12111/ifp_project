from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

from requirement_management.models import User, Requirement, Report, RequirementDefect, Quotation

INVOICE_STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('submitted', 'Submitted'),
    ('sent_to_customer', 'Sent to Customer'),
    ('paid', 'Paid'),
]

# Create your models here.
class Invoice(models.Model):
    """
    Model representing an invoice.

    Attributes:
        user (ForeignKey to User): The user who created the invoice.
        customer (ForeignKey to User): The customer associated with the invoice.
        requirement (ForeignKey to Requirement): The requirement related to the invoice.
        report (ForeignKey to Report): The report associated with the invoice.
        defects (ManyToManyField to RequirementDefect): Defects related to the invoice.
        quotation (ForeignKey to Quotation): The quotation related to the invoice.
        invoice_json (JSONField): Detailed JSON data including SOR and defects.
        total_amount (DecimalField): The total payable amount.
        status (CharField): The status of the invoice.
        submitted_at (DateTimeField): Date and time when the invoice was submitted.
        pdf_path (CharField): Path to the PDF document of the invoice stored in S3.
        created_at (DateTimeField): Date and time when the invoice was created.
        updated_at (DateTimeField): Date and time when the invoice was last updated.

    Meta:
        verbose_name (str): A human-readable name for the model.
        verbose_name_plural (str): A human-readable plural name for the model.
        ordering (list): The default ordering for querysets of this model.

    Methods:
        __str__(): Returns a string representation of the invoice.
        get_absolute_url(): Returns the absolute URL of the invoice detail view.
    """

    # User relations
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("Created By"))
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="customer", verbose_name=_("Customer"))
    
    # Requirements (FRA) Relations
    requirement = models.ForeignKey(Requirement, on_delete=models.CASCADE, verbose_name=_("Requirement"))
    report = models.ForeignKey(Report, on_delete=models.CASCADE, verbose_name=_("Report"))
    defects = models.ManyToManyField(RequirementDefect, verbose_name=_("Defects"))
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, verbose_name=_("Quotation"))
    
    # Detailed JSON with SOR and Defects
    invoice_json = models.JSONField(verbose_name=_("Invoice Details"))  # This field stores JSON data

    # Detailed JSON with SOR and Defects
    billing_information_json = models.JSONField(verbose_name=_("Billing Information Details"), default=dict)  # This field stores JSON data
    
    # Payable Total Amount
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Total Amount"))
    
    # Status of the Invoive
    status = models.CharField(max_length=30, choices=INVOICE_STATUS_CHOICES, default='draft', verbose_name=_("Status"))
    
    # Invoice Submitted Date time
    submitted_at = models.DateTimeField(auto_now_add=False, auto_now=False, null=True, blank=True, verbose_name=_("Submitted At"))

    # Invoice Paid Date Time
    paid_at = models.DateTimeField(auto_now_add=False, auto_now=False, null=True, blank=True, verbose_name=_("Paid At"))
    
    # Invoice PDF document saved on s3's path
    pdf_path = models.CharField(max_length=500, null=True, blank=True, verbose_name=_("Invoice PDF Path"))
    
    # Creation and Updation details
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        """
        Metadata options for the Invoice model.

        Attributes:
            verbose_name (str): A human-readable name for the model.
            verbose_name_plural (str): A human-readable plural name for the model.
            ordering (list): The default ordering for querysets of this model.
        """
        verbose_name = _("Invoice")
        verbose_name_plural = _("Invoices")
        ordering =['-updated_at']
    
    def __str__(self):
        """
        Returns a string representation of the invoice.
        
        Returns:
            str: A string representing the invoice.
        """
        return f'Invoice - {self.pk}'

    def get_absolute_url(self):
        """
        Returns the absolute URL of the invoice detail view.
        
        Returns:
            str: The absolute URL of the invoice detail view.
        """
        return reverse("view_customer_invoice", kwargs={"pk": self.pk, "customer_id": self.customer.id})
