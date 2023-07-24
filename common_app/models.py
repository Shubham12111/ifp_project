from django.db import models
from django.contrib.auth.models import Group

class MenuItem(models.Model):
    permission_required = models.BooleanField(default=False)
    name = models.CharField(max_length=100)
    url = models.CharField(max_length=200)
    icon = models.CharField(max_length=100)
    order = models.IntegerField()
    
    # Many-to-many relationship with Permission model
    permissions = models.ManyToManyField(Group, blank=True)

    # Self-referencing ForeignKey for sub-menu functionality
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.CASCADE)

    def __str__(self):
        return self.name