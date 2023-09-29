from django.contrib import admin
from . models import STW 

# Register your models here.


class STWAdmin(admin.ModelAdmin):
    """
    Admin class for the STW model.

    Attributes:
        list_display (tuple): A tuple of fields to be displayed in the list view of the admin panel.
    """
    list_display = ('user_id', 'action', 'description', 'status', 'RBNO')


admin.site.register(STW,STWAdmin)