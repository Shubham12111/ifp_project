from django.contrib import admin
from .models import Requirement,RequirementAsset, RequirementDefect, RequirementDefectDocument,Report, SOR, SORImage

# Register your models here.

class RequirementAdmin(admin.ModelAdmin):
    """
    Admin class for the Requirement model.

    Attributes:
        list_display (tuple): A tuple of fields to be displayed in the list view of the admin panel.
    """
    list_display = ('user_id', 'customer_id', 'description', 'quantity_surveyor', 'status')


class RequirementDefectAdmin(admin.ModelAdmin):
    """
    Admin class for the RequirementDefect model.

    Attributes:
        list_display (tuple): A tuple of fields to be displayed in the list view of the admin panel.
    """
    list_display = ('requirement_id', 'action', 'description', )


class RequirementDefectDocumentAdmin(admin.ModelAdmin):
    """
    Admin class for the RequirementDefectDocument model.

    Attributes:
        list_display (tuple): A tuple of fields to be displayed in the list view of the admin panel.
    """
    list_display = ('requirement_id', 'defect_id', 'document_path')


admin.site.register(Requirement, RequirementAdmin)
admin.site.register(RequirementDefect, RequirementDefectAdmin)
admin.site.register(SOR)
admin.site.register(SORImage)
admin.site.register(RequirementDefectDocument, RequirementDefectDocumentAdmin)
admin.site.register(RequirementAsset)
admin.site.register(Report)