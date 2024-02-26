from django.db import models
from authentication.models import User
from cities_light.models import City, Country, Region
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

class BillingAddress(models.Model):
    """
    Billing Addresss model    
    """
    user_id = models.ForeignKey("authentication.User", on_delete=models.CASCADE)
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
    
    user_id = models.ForeignKey("authentication.User", on_delete=models.CASCADE)
    
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
    
    """
    Contact Person model
    """
    
    user_id = models.ForeignKey("authentication.User", on_delete=models.CASCADE)
    first_name = models.CharField(max_length=127)
    last_name = models.CharField(max_length=127) 
    email = models.EmailField(max_length=254)
    phone_number = models.CharField(max_length=127)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    job_role = models.TextField(max_length=254, null= True)

    class Meta:
        ordering =['id']
    