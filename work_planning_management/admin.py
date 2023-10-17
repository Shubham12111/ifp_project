from django.contrib import admin

from . models import Job, STWRequirements,STWAsset,STWDefect,STWDefectDocument,RLO,RLOLetterTemplate


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


class JobAdmin(admin.ModelAdmin):
    """
    Admin class for the Job model.

    Attributes:
        list_display (tuple): A tuple of fields to be displayed in the list view of the admin panel.
    """
    list_display = ('quotation', 'created_at', 'updated_at')

class RLOAdmin(admin.ModelAdmin):
    """
    Admin class for the RLO model.

    Attributes:
        list_display (tuple): A tuple of fields to be displayed in the list view of the admin panel.
    """
    list_display = ('user_id','name','status', 'created_at', 'updated_at')



admin.site.register(STWRequirements,STWRequirementsAdmin)
admin.site.register(STWAsset)
admin.site.register(STWDefect, STWDefectAdmin)
admin.site.register(STWDefectDocument, STWDefectDocumentAdmin)
admin.site.register(Job, JobAdmin)
admin.site.register(RLO, RLOAdmin)
admin.site.register(RLOLetterTemplate)

