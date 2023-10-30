from django.contrib import admin

from . models import Job, STWRequirements,STWAsset,STWDefect,STWDefectDocument,RLO,RLOLetterTemplate,SitepackDocument,SitepackAsset,STWJob,Team,Member,JobDocument




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

class SitepackAssetAdmin(admin.ModelAdmin):
    list_display = ('id','sitepack_id','document_path' )


class JobDocumentAdmin(admin.ModelAdmin):
    list_display = ('job', 'sitepack_document', 'created_at', 'updated_at')
  

admin.site.register(STWRequirements,STWRequirementsAdmin)
admin.site.register(STWAsset)
admin.site.register(STWDefect, STWDefectAdmin)
admin.site.register(STWDefectDocument, STWDefectDocumentAdmin)
admin.site.register(SitepackDocument)
admin.site.register(SitepackAsset,SitepackAssetAdmin) 
admin.site.register(Job, JobAdmin)
admin.site.register(RLO, RLOAdmin)
admin.site.register(RLOLetterTemplate)
admin.site.register(STWJob)
# admin.site.register(STWJobAssignment)
admin.site.register(Member, MemberAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(JobDocument,JobDocumentAdmin)



