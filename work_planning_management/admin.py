from django.contrib import admin

from . models import STW ,Job, STWRequirements,STWAsset,STWDefect,STWDefectDocument


# Register your models here.

from . models import STW 


class STWRequirementsAdmin(admin.ModelAdmin):
    """
    Admin class for the STW model.

    Attributes:
        list_display (tuple): A tuple of fields to be displayed in the list view of the admin panel.
    """
    list_display = ('user_id','customer_id', 'action', 'description', 'status', 'RBNO')

class STWDefectAdmin(admin.ModelAdmin):
    """
    Admin class for the STWDefect model.

    Attributes:
        list_display (tuple): A tuple of fields to be displayed in the list view of the admin panel.
    """
    list_display = ('stw_id', 'action', 'description', )


class STWDefectDocumentAdmin(admin.ModelAdmin):
    """
    Admin class for the STWDefectDocument model.

    Attributes:
        list_display (tuple): A tuple of fields to be displayed in the list view of the admin panel.
    """
    list_display = ('stw_id', 'defect_id', 'document_path')


admin.site.register(STWRequirements,STWRequirementsAdmin)
admin.site.register(STWAsset)
admin.site.register(STWDefect, STWDefectAdmin)
admin.site.register(STWDefectDocument, STWDefectDocumentAdmin)

admin.site.register(STW,STWAdmin)

admin.site.register(STW,STWAdmin)

class JobAdmin(admin.ModelAdmin):
    list_display = ('quotation', 'created_at', 'updated_at') 
    list_filter = ('created_at', 'updated_at') 
    search_fields = ('quotation__title',) 
admin.site.register(Job, JobAdmin)

