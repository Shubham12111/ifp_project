from django.contrib import admin
from .models import *

# Register your models here.

class RequirementAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'customer_id', 'description', 'quantity_surveyor', 'status')


class RequirementDefectAdmin(admin.ModelAdmin):
    list_display = ('requirement_id', 'action', 'description', )


class RequirementDefectDocumentAdmin(admin.ModelAdmin):
    list_display = ('requirement_id', 'defect_id', 'document_path')



@admin.register(SORItem)
class SORItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'customer_id', 'category_id', 'price', 'created_at', 'updated_at')
    list_filter = ('customer_id', 'category_id', 'created_at')
    search_fields = ('name', 'reference_number', 'user_id__email')
    
@admin.register(SORCategory)
class SORCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user_id', 'status', 'created_at', 'updated_at')
    list_filter = ('user_id', 'status', 'created_at')
    search_fields = ('name',)
    
admin.site.register(Requirement, RequirementAdmin)
admin.site.register(RequirementDefect, RequirementDefectAdmin)
admin.site.register(SORItemImage)
admin.site.register(RequirementDefectDocument, RequirementDefectDocumentAdmin)
admin.site.register(RequirementAsset)
admin.site.register(Report)