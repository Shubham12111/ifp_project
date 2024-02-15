from typing import Any
from django.contrib import admin
from django.db.models.query import QuerySet
from django.http.request import HttpRequest

from . models import Job, STWRequirements,STWAsset,STWDefect,STWDefectDocument,RLO,RLOLetterTemplate,Team,Member,JobDocument,Events,SitePack
from work_planning_management.forms import SitePackAdminForm, delete_file_from_s3

class STWRequirementsAdmin(admin.ModelAdmin):
    """
    Admin class for the  model.

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


class RLOAdmin(admin.ModelAdmin):
    """
    Admin class for the RLO model.

    Attributes:
        list_display (tuple): A tuple of fields to be displayed in the list view of the admin panel.
    """
    list_display = ('user_id','name','status', 'created_at', 'updated_at')


class MemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'trade_type', 'mobile_number', 'email', 'job_title')
    list_filter = ('trade_type', 'job_title')
    search_fields = ('name', 'trade_type', 'email')
    list_per_page = 10

class TeamAdmin(admin.ModelAdmin):
    list_display = ('team_name', 'members_list')
    search_fields = ('team_name',)

    def members_list(self, obj):
        return ", ".join([member.name for member in obj.members.all()])

    members_list.short_description = 'Members'



class JobAdmin(admin.ModelAdmin):
    list_display = ('quotation', 'created_at', 'updated_at') 
    list_filter = ('created_at', 'updated_at') 
    search_fields = ('quotation__title',)

class SitePackAdmin(admin.ModelAdmin):
    
    list_display = ('id','name', 'orignal_document_name', 'create_at',)
    form = SitePackAdminForm

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        queryset = super().get_queryset(request)

        if request.user.is_staff and not request.user.is_superuser:
            return queryset.filter(user_id__is_staff=True).all()

        return queryset

    def delete_queryset(self, request, queryset) -> None:
        for obj in queryset:
            deleted = delete_file_from_s3(obj.document_path, f'sitepack_doc')
        return super().delete_queryset(request, queryset)
    
    def delete_model(self, request, obj) -> None:
        deleted = delete_file_from_s3(obj.document_path, f'sitepack_doc')
        return super().delete_model(request, obj)

class JobDocumentAdmin(admin.ModelAdmin):
    list_display = ('job', 'sitepack_document', 'created_at', 'updated_at')
  

admin.site.register(STWRequirements,STWRequirementsAdmin)
admin.site.register(STWAsset)
admin.site.register(STWDefect, STWDefectAdmin)
admin.site.register(STWDefectDocument, STWDefectDocumentAdmin)
admin.site.register(RLO, RLOAdmin)
admin.site.register(RLOLetterTemplate)
admin.site.register(Member, MemberAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(JobDocument,JobDocumentAdmin)
admin.site.register(Events)
admin.site.register(SitePack, SitePackAdmin)
admin.site.register(Job)