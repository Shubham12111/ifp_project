from django.db import models
from ckeditor.fields import RichTextField
from cities_light.models import City, Country, Region

from authentication.models import User


TAX_PREFERENCE_CHOICES = (
    ('taxable', 'Taxable'),
    ('tax_exempt', 'Tax Exempt'),
)

VENDOR_STATUS_CHOICES =(
     ('pending', 'Pending'),
     ('in-progress', 'In Progress'),
     ('completed', 'Completed')
)


# Create your models here.
class Vendor(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vendor_user')
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20)
    company = models.CharField(max_length=255,null=True,blank=True)
    vat_number = models.CharField(max_length=20,null=True,blank=True)
    pan_number = models.CharField(max_length=20,null=True,blank=True)
    tax_preference = models.CharField(max_length=30, choices=TAX_PREFERENCE_CHOICES,null=True, blank=True)
    address = models.CharField(max_length=255,null=True,blank=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, null=True, blank=True)
    town = models.ForeignKey(City, on_delete=models.CASCADE, null=True, blank=True)
    county = models.ForeignKey(Region, on_delete=models.CASCADE, null=True, blank=True, verbose_name="County")
    post_code = models.CharField(max_length=10, null=True, blank=True)
    vendor_status = models.CharField(max_length=30, choices=VENDOR_STATUS_CHOICES,null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.email