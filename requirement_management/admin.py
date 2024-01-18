from django.contrib import admin
from .models import *
from import_export.admin import ImportExportModelAdmin
from django.contrib import admin 
from .resource import SORItemUpload

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
    list_display = ('name', 'customer_id','reference_number', 'category_id', 'price','units', 'created_at', 'updated_at')
    list_filter = ('customer_id', 'category_id', 'created_at')
    search_fields = ('name', 'reference_number', 'user_id__email')

@admin.register(SORItemProxy)
class SORItemProxyAdmin(ImportExportModelAdmin):
    resource_class = SORItemUpload  
    list_display = ('name', 'category_id', 'reference_number','price','units', 'created_at', 'updated_at')
    list_filter = ( 'category_id', 'created_at')
    search_fields = ('name', 'reference_number', 'user_id__email')

    exclude = ['customer_id', 'user_id']
    def get_queryset(self, request):
        # Override the queryset to show only instances where customer_id is NULL
        """
        Return a QuerySet of all model instances that can be edited by the
        admin site.
        """
        queryset = super().get_queryset(request)
        return queryset.filter(customer_id__isnull=True)
    
    def save_form(self, request, form, change):
        """
        Overrides the save_form method to ensure the instance is marked as an user.

        Args:
            request (Any): The request object.
            form (Any): The form instance.
            change (Any): Indicates if it's a change to an existing instance.

        Returns:
            Any: The saved instance after modification.
        """
        instance = super().save_form(request, form, change)
        if not instance.user_id:
            instance.user_id = request.user
            instance.save()
        return instance

       
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
