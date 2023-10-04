from django.contrib import admin
from . models import STWRequirements,STWAsset,STWDefect,STWDefectDocument

# Register your models here.


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


