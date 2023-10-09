from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from cities_light.models import City, Country, Region
from ckeditor.fields import RichTextField


# Choices for the can_access field
ACCESS_CHOICES = [
    ('self', 'Self'),
    ('all', 'All'),
    ('none', 'None'),
]

MODULE_CHOICES = [
    ('contact', 'Contacts'),
    ('task', 'Task'),
    ('customer', 'Customer'),
    ('estimation', 'Estimation'),
    ('fire_risk_assessment', 'Fire Risk Assessment'),
    ('survey', 'Survey (Scheduling)'),
    ('stock_management', 'Stock Management'),
    ('invoicing', 'Invoicing'),
    ('purchase_order', 'Purchase Order'),
]

CUSTOMER_TYPES = (
    ('business', 'Business'),
    ('individual', 'Individual'),
)

ROLE_CHOICES = (
    ('Customer', 'Customer'),
    ('contractor', 'Contractor'),
    ('sale_executive', 'Sale Executive'),
    ('quantity_surveyor', 'Quantity Surveyor'),
    ('surveyor', 'Surveyor'),
    ('estimator', 'Estimator'),
    ('project_manager/contract_manager', 'Project Manager/Contract Manager'),
    ('projects_coordinator', 'Projects Coordinator'),
    ('projects_RLO', 'Projects RLO'),
    ('financial_manager', 'Financial Manager'),
    ('projects_admin_(IT)', 'Projects Admin (IT)'),
    ('supervisor', 'Supervisor'),
    ('snagging_supervisor', 'Snagging Supervisor'),
    ('quality_assurance', 'Quality Assurance'),
    ('sub-contractor', 'Sub-Contractor'),
)

class UserRole(models.Model):
    """
    Represents a user role with associated permissions.

    Attributes:
        name (str): The name of the user role. This should be unique.
        description (str): A description of the user role.
    """

    # CharField for the 'name' field
    name = models.CharField(max_length=100, choices=ROLE_CHOICES, unique=True)

    # CharField for the 'description' field
    description = RichTextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,null=True)

    class Meta:
        """
        Meta class for defining additional properties of the model.
        """
        verbose_name = "User Role"
        verbose_name_plural = "User Roles"
        # You can define any additional properties specific to the model here.
        # For example, you can set the default ordering for the model's queryset.
        ordering = ['name']
        
    def __str__(self):
        """
        Returns a string representation of the user role.

        Returns:
            str: The name of the user role.
        """
        return self.name

class UserRolePermission(models.Model):
    """
    Represents a custom role permission.

    Attributes:
        role (ForeignKey): The foreign key relation to the UserRole model.
        module (CharField): The choice field for selecting the module.
        can_list_data (BooleanField): Indicates whether users with this permission can list data.
        can_create_data (BooleanField): Indicates whether users with this permission can create data.
        can_change_data (BooleanField): Indicates whether users with this permission can change data.
        can_view_data (BooleanField): Indicates whether users with this permission can view data.
        can_delete_data (BooleanField): Indicates whether users with this permission can delete data.
        access_list_data (CharField): The choice field for selecting access level for listing data ("self" or "all").
        access_change_data (CharField): The choice field for selecting access level for changing data ("self" or "all").
        access_view_data (CharField): The choice field for selecting access level for viewing data ("self" or "all").
        access_delete_data (CharField): The choice field for selecting access level for deleting data ("self" or "all").
    """

    # Foreign Key to UserRole model
    role = models.ForeignKey(UserRole, on_delete=models.CASCADE)
    module = models.CharField(max_length=100, choices=MODULE_CHOICES)

    #permissions
    can_create_data = models.BooleanField(verbose_name="Create")
    can_list_data = models.CharField(max_length=100, choices=ACCESS_CHOICES, verbose_name="List",default='self')
    can_change_data = models.CharField(max_length=100, choices=ACCESS_CHOICES, verbose_name="Change",default='self')
    can_view_data = models.CharField(max_length=100, choices=ACCESS_CHOICES, verbose_name="View",default='self')
    can_delete_data = models.CharField(max_length=100, choices=ACCESS_CHOICES, verbose_name="Delete",default='self')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.role} - {self.module}"

    class Meta:
        # Enforce uniqueness of role and module together
        unique_together = ['role', 'module']
  
class UserManager(BaseUserManager):
    """
    Custom manager for the User model.

    Provides methods to create regular users and superusers.
    """
    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a regular user.

        Args:
            email (str): The user's email address.
            password (str): The user's password.
            **extra_fields: Additional user fields.

        Returns:
            User: The created user.

        Raises:
            ValueError: If the email is not provided.
        """
        if not email:
            raise ValueError('The Email field must be set')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and save a superuser.

        Args:
            email (str): The superuser's email address.
            password (str): The superuser's password.
            **extra_fields: Additional superuser fields.

        Returns:
            User: The created superuser.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model with email as the unique identifier.

    Provides additional fields for user information.
    """
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    address = models.CharField(max_length=255 , null=True, blank=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, null=True, blank=True)
    town = models.ForeignKey(City, on_delete=models.CASCADE, null=True, blank=True , verbose_name="Town" )
    county = models.ForeignKey(Region, on_delete=models.CASCADE, null=True, blank=True, verbose_name="County")
    post_code = models.CharField(max_length=10, null=True, blank=True)

    # relationship with UserRole
    company_name = models.CharField(max_length=100, blank=True, null=True)
    customer_type = models.CharField(max_length=10, choices=CUSTOMER_TYPES, default='individual')
    roles = models.ForeignKey(UserRole,on_delete=models.PROTECT, null=True,verbose_name="UserRole")
    created_by = models.ForeignKey("self", on_delete=models.PROTECT, null=True, blank=True, related_name='created_users')
    enforce_password_change = models.BooleanField(default = False)
    
    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email
    

