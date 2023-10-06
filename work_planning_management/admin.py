from django.contrib import admin
from . models import STW ,Job

# Register your models here.


class STWAdmin(admin.ModelAdmin):
    """
    Admin class for the STW model.

    Attributes:
        list_display (tuple): A tuple of fields to be displayed in the list view of the admin panel.
    """
    list_display = ('user_id', 'action', 'description', 'status', 'RBNO')


admin.site.register(STW,STWAdmin)

class JobAdmin(admin.ModelAdmin):
    list_display = ('quotation', 'created_at', 'updated_at') 
    list_filter = ('created_at', 'updated_at') 
    search_fields = ('quotation__title',) 
admin.site.register(Job, JobAdmin)