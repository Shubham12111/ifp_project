from django.db import models
from django.utils.translation import gettext_lazy as _

from authentication.models import User
from customer_management.models import SiteAddress


STW_CHOICES = (
    ('active', 'Active'),
    ('pending', 'Pending'),
    ('completed', 'Completed')
)

class STW(models.Model):
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
    UPRN = models.CharField(max_length=255, null=True)
    RBNO = models.CharField(max_length=255, null=True)
    description = models.TextField()
    action = models.TextField()
    site_address =  models.ForeignKey(SiteAddress, on_delete=models.CASCADE, null=True)
    status = models.CharField(max_length=30,choices = STW_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('STW')
        verbose_name_plural = _('STW')

    def __str__(self):
        return f"{self.user_id.first_name} {self.user_id.last_name}'s STW"


