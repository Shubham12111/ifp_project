from django.db import models
from django.utils.translation import gettext_lazy as _

from cities_light.models import City, Country, Region

from authentication.models import User
from customer_management.constants import POST_CODE_LIST

TAX_PREFERENCE_CHOICES = (
    ('taxable', 'Taxable'),
    ('tax_exempt', 'Tax Exempt'),
)

PAYMENT_TERMS_CHOICES = (
    ('30 days', '30 Days'),
    ('45 days', '45 Days'),
    ('60 days', '60 Days'),
    )

CUSTOMER_TYPES = (
    ('public sector-NHS', 'Public Sector-NHS'),
    ('public Sector-social housing', 'Public Sector-Social Housing'),
    ('private Sector-social housing', 'Private Sector-Social Housing'),
    ('facilities management', 'Facilities Management'),
    ('commercial client', 'Commercial Client'),
    ('private client', 'Private Client'),
)

class CustomerMeta(models.Model):
    """
    A model representing a customer.

    This model stores information about a customer, including their company details,
    addresses, contact information, and customer type.

    Attributes:
        company_name (CharField): The name of the customer's company.
        company_registration_number (CharField): The registration number of the customer's company.
        registered_address (CharField, optional): The registered address of the customer.
        registered_country (CharField, optional): The registered country of the customer.
        registered_town (CharField, optional): The registered town of the customer.
        registered_county (CharField, optional): The registered county of the customer.
        registered_post_code (CharField, optional): The registered post code of the customer.
        trading_address (CharField, optional): The trading address of the customer.
        trading_country (CharField, optional): The trading country of the customer.
        trading_town (CharField, optional): The trading town of the customer.
        trading_county (CharField, optional): The trading county of the customer.
        trading_post_code (CharField, optional): The trading post code of the customer.
        utr_number (CharField): The Unique Taxpayer Reference (UTR) number of the customer.
        main_telephone_number (CharField): The main telephone number of the customer.
        email_address (EmailField): The email address of the customer.
        customer_type (CharField): The type of customer (e.g., public sector, NHS).

    Meta:
        verbose_name (str): A human-readable name for the model.
        verbose_name_plural (str): A human-readable plural name for the model.

    Methods:
        __str__: Returns a string representation of the customer.
    """

    user_id = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=100, verbose_name=_("Company Name"))
    company_registration_number = models.CharField(max_length=255, verbose_name=_("Company Registration Number"))

    registered_address = models.CharField(max_length=255, null=True, blank=True, verbose_name=_("Registered Address"))
    registered_country = models.CharField(max_length=255, null=True, blank=True, verbose_name=_("Registered Country"))
    registered_town = models.CharField(max_length=255, null=True, blank=True, verbose_name=_("Registered Town"))
    registered_county = models.CharField(max_length=255, null=True, blank=True, verbose_name=_("Registered County"))
    registered_post_code = models.CharField(max_length=10, choices=POST_CODE_LIST, null=True, blank=True, verbose_name=_("Registered Post Code"))

    trading_address = models.CharField(max_length=255, null=True, blank=True, verbose_name=_("Trading Address"))
    trading_country = models.CharField(max_length=255, null=True, blank=True, verbose_name=_("Trading Country"))
    trading_town = models.CharField(max_length=255, null=True, blank=True, verbose_name=_("Trading Town"))
    trading_county = models.CharField(max_length=255, null=True, blank=True, verbose_name=_("Trading County"))
    trading_post_code = models.CharField(max_length=10, choices=POST_CODE_LIST, null=True, blank=True, verbose_name=_("Trading Post Code"))

    utr_number = models.CharField(max_length=255, verbose_name=_("UTR Number"), null=True)
    main_telephone_number = models.CharField(max_length=125, verbose_name=_("Main Telephone Number"))
    email = models.EmailField(max_length=255, verbose_name=_("Email Address"))
    customer_type = models.CharField(max_length=100, choices=CUSTOMER_TYPES, default='public sector-NHS', verbose_name=_("Customer Type"))

    class Meta:
        verbose_name = _("Customer")
        verbose_name_plural = _("Customers")
        # Define the combination of fields that should be unique together
        unique_together = ('user_id', 'company_name')

    def __str__(self):
        """
        Returns a string representation of the customer.

        Returns:
            str: The company name of the customer.
        """
        return self.company_name

class BillingAddress(models.Model):
    """
    Billing Addresss model    
    """
    user_id = models.ForeignKey("authentication.User", on_delete=models.CASCADE, null=True)
    vat_number= models.CharField(max_length=200, null=True, blank=True)
    #pan_number = models.CharField(max_length=200, null=True, blank=True)
    place_to_supply = models.CharField(max_length=200, null=True, blank=True)
    tax_preference = models.CharField(max_length=20, choices=TAX_PREFERENCE_CHOICES, null=True, blank=True)
    address = models.CharField(max_length=255 , null=True, blank=True)
    country = models.CharField(max_length=255, null=True, blank=True)
    town = models.CharField(max_length=255, null=True, blank=True)
    county = models.CharField(max_length=255, null=True, blank=True)
    post_code = models.CharField(max_length=10, choices=POST_CODE_LIST, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    contact_name = models.CharField(max_length=127,null=True)
    contact_email = models.EmailField(max_length=254, null=True)
    contact_tel_no = models.CharField(max_length=127,null=True)
    payment_terms = models.CharField(max_length=20, choices=PAYMENT_TERMS_CHOICES, null=True, blank=True)
    purchase_order_required = models.BooleanField(
        default=True,  
        verbose_name='Is a Purchase Order number required?'
    )  
    CIS = models.BooleanField(
        default=True
    )


    class Meta:
        ordering =['id']
    
class SiteAddress(models.Model):
    
    """
    Site Address model
    """
    
    user_id = models.ForeignKey("authentication.User", on_delete=models.CASCADE, null=True)
    
    address = models.CharField(max_length=255 , null=True, blank=True)
    site_name = models.CharField(max_length=255 , null=True, blank=True)
    country = models.CharField(max_length=255, null=True, blank=True)
    town = models.CharField(max_length=255, null=True, blank=True)
    county = models.CharField(max_length=255, null=True, blank=True)
    post_code = models.CharField(max_length=10, choices=POST_CODE_LIST, null=True, blank=True)
    UPRN = models.CharField(max_length=10 , null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
   
    def __str__(self):
        return self.site_name
    
    class Meta:
        ordering =['id']

class ContactPerson(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    customer = models.ForeignKey(CustomerMeta, on_delete=models.CASCADE, null=True)
    job_role = models.TextField(max_length=254, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Contact Person")
        verbose_name_plural = _("Contact Persons")