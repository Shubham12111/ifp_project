from django.contrib import admin
from .models import Requirement, RequirementDefect, RequirementDocument

# Register your models here.

class RequirementAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'customer_id', 'description', 'UPRN', 'requirement_date_time', 'quality_surveyor', 'status')


class RequirementDefectAdmin(admin.ModelAdmin):
    list_display = ('requirement_id', 'action', 'description', 'defect_period', 'due_date', 'status')


class RequirementDocumentAdmin(admin.ModelAdmin):
    list_display = ('requirement_id', 'defect_id', 'document_path')


admin.site.register(Requirement, RequirementAdmin)
admin.site.register(RequirementDefect, RequirementDefectAdmin)
admin.site.register(RequirementDocument, RequirementDocumentAdmin)
 



