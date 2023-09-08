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

CATEGORY_STATUS_CHOICES = (
        ('active', 'Active'),
        ('in-active', 'Inactive'),
)

PRODUCT_STATUS_CHOICES = (

        ('active', 'Active'),
        ('expired', 'Expired'),
)

ITEM_TYPE_CHOICES = (
        ('item', 'Item'),
        ('sor', 'SOR'),
    )
SALUTATION_CHOICES = [
        ('Mr.', 'Mr.'),
        ('Mrs.', 'Mrs.'),
        ('Miss', 'Miss'),
    ]



UNIT_CHOICES = (
    ('single', 'Single Unit'),
    ('box', 'Box'),
    ('mm', 'mm'),
)

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
    billing_phone_number = models.CharField(max_length=20, null=True, blank=True)
    vendor_status = models.CharField(max_length=30, choices=VENDOR_STATUS_CHOICES,null=True, blank=True)
    remarks = RichTextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.email
    
class VendorContactPerson(models.Model):
    
    """
    Vendor Contact Person model
    """
    
    vendor_id = models.ForeignKey(Vendor, on_delete=models.CASCADE, verbose_name="Vendor")
    salutation = models.CharField(max_length=10, choices=SALUTATION_CHOICES,)
    first_name = models.CharField(max_length=127)
    last_name = models.CharField(max_length=127) 
    email = models.EmailField(max_length=254)
    phone_number = models.CharField(max_length=127)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.email

class Category(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='category_user')
    name = models.CharField(max_length=50)
    description = RichTextField(null=True)
    image_path = models.CharField(max_length=255)
    status = models.CharField(max_length=50, choices=CATEGORY_STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class Item(models.Model):
    vendor_id = models.ForeignKey(Vendor, on_delete=models.CASCADE, null=True ,verbose_name="Vendor")
    category_id = models.ForeignKey(Category, on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    item_name = models.CharField(max_length=50)
    description =  RichTextField(null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    reference_number = models.CharField(max_length=50)
    units = models.CharField(max_length=10, choices=UNIT_CHOICES, default='single')
    quantity_per_box = models.DecimalField(max_digits=10, default=1.0, decimal_places=2)
    item_type = models.CharField(max_length=10, choices=ITEM_TYPE_CHOICES, default='item')
    status = models.CharField(max_length=50, choices=PRODUCT_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.item_name

class ItemImage(models.Model):
    item_id = models.ForeignKey(Item, on_delete=models.CASCADE, null=True)
    image_path = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Image for {self.item_id.name}"

class InventoryLocation(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = RichTextField(null=True)
    address = models.CharField(max_length=255)
    town = models.ForeignKey(City, on_delete=models.CASCADE)
    county = models.ForeignKey(Region, on_delete=models.CASCADE)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    post_code = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Inventory(models.Model):
    item_id = models.ForeignKey(Item, on_delete=models.CASCADE,null=True)
    inventory_location = models.ForeignKey(InventoryLocation, on_delete=models.CASCADE)
    total_inventory = models.DecimalField(max_digits=10, decimal_places=2)
    assigned_inventory = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)