from django.contrib import admin
from .models import MenuItem, EmailNotificationTemplate,AdminConfiguration,SORValidity,UpdateWindowConfiguration



class MenuItemInline(admin.StackedInline):
    model = MenuItem
    extra = 0
    fk_name = 'parent'

class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'icon', 'order', 'permission_required')
    list_filter = ('permission_required',)
    search_fields = ('name', 'url')
    inlines = [MenuItemInline]
    
    def get_queryset(self, request):
        """
        Return the queryset for the admin list view with custom ordering.
        """
        return super().get_queryset(request).order_by('order')

@admin.register(EmailNotificationTemplate)
class EmailNotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ('subject', 'recipient', 'purpose')
    list_filter = ('purpose',)
    search_fields = ('subject', 'recipient')


@admin.register(AdminConfiguration)
class AdminConfigurationAdmin(admin.ModelAdmin):
    list_display = ('tax_rate',)


class SORValidityAdmin(admin.ModelAdmin):
    list_display = ('id', 'sor_expiration_date', 'is_expired', 'is_within_update_window')
    list_filter = ('sor_expiration_date',)


@admin.register(UpdateWindowConfiguration)
class UpdateWindowConfigurationAdmin(admin.ModelAdmin):
    list_display = ('start_date', 'end_date', 'is_active')


admin.site.register(MenuItem, MenuItemAdmin)
admin.site.register(SORValidity, SORValidityAdmin)