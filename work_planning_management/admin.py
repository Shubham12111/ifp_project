from django.contrib import admin

from . models import Job, STWRequirements,STWAsset,STWDefect,STWDefectDocument,RLO,RLOLetterTemplate,SitepackDocument,SitepackAsset,STWJob



class STWRequirementsAdmin(admin.ModelAdmin):
    """
    Admin class for the STW model.

    Attributes:
        list_display (tuple): A tuple of fields to be displayed in the list view of the admin panel.
    """
    list_display = ('building_name','postcode', 'action', 'description', 'status', 'RBNO')

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

class STWJobAdmin(admin.ModelAdmin):
    """
    Admin class for the stw JOB model.

    Attributes:
        list_display (tuple): A tuple of fields to be displayed in the list view of the admin panel.
    """
    list_display = ('stw', 'created_at', 'updated_at')


class RLOAdmin(admin.ModelAdmin):
    """
    Admin class for the RLO model.

    Attributes:
        list_display (tuple): A tuple of fields to be displayed in the list view of the admin panel.
    """
    list_display = ('user_id','name','status', 'created_at', 'updated_at')

class JobAdmin(admin.ModelAdmin):
    list_display = ('quotation', 'created_at', 'updated_at') 
    list_filter = ('created_at', 'updated_at') 
    search_fields = ('quotation__title',)

admin.site.register(STWRequirements,STWRequirementsAdmin)
admin.site.register(STWAsset)
admin.site.register(STWDefect, STWDefectAdmin)
admin.site.register(STWDefectDocument, STWDefectDocumentAdmin)
admin.site.register(STWJob,STWJobAdmin)
admin.site.register(SitepackDocument)
admin.site.register(SitepackAsset) 
admin.site.register(Job, JobAdmin)
admin.site.register(RLO, RLOAdmin)
admin.site.register(RLOLetterTemplate)



