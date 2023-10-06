from django.contrib import admin
from .models import *

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


@admin.register(SORItem)
class SORItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'customer_id', 'category_id', 'price','units', 'created_at', 'updated_at')
    list_filter = ('customer_id', 'category_id', 'created_at')
    search_fields = ('name', 'reference_number', 'user_id__email')
    
@admin.register(SORCategory)
class SORCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user_id', 'status', 'created_at', 'updated_at')
    list_filter = ('user_id', 'status', 'created_at')
    search_fields = ('name',)


class QuotationAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'customer_id', 'requirement_id', 'report_id', 'status', 'created_at', 'updated_at')
    list_filter = ('status',)
    search_fields = ('user_id__username', 'customer_id__username', 'requirement_id__name', 'report_id__name')
    readonly_fields = ('created_at', 'updated_at')
    # You can customize other admin options here

admin.site.register(Quotation, QuotationAdmin)
admin.site.register(Requirement, RequirementAdmin)
admin.site.register(RequirementDefect, RequirementDefectAdmin)
admin.site.register(SORItemImage)
admin.site.register(RequirementDefectDocument, RequirementDefectDocumentAdmin)
admin.site.register(RequirementAsset)
admin.site.register(Report)