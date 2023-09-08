from django.contrib import admin
from .models import Requirement,RequirementAsset, RequirementDefect, RequirementDefectDocument,Report

# Register your models here.

class RequirementAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'customer_id', 'description', 'quantity_surveyor', 'status')


class RequirementDefectAdmin(admin.ModelAdmin):
    list_display = ('requirement_id', 'action', 'description', )


class RequirementDefectDocumentAdmin(admin.ModelAdmin):
    list_display = ('requirement_id', 'defect_id', 'document_path')


admin.site.register(Requirement, RequirementAdmin)
admin.site.register(RequirementDefect, RequirementDefectAdmin)
admin.site.register(RequirementDefectDocument, RequirementDefectDocumentAdmin)
admin.site.register(RequirementAsset)
admin.site.register(Report)