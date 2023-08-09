from django.contrib import admin
from .models import MenuItem, EmailNotificationTemplate

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


admin.site.register(MenuItem, MenuItemAdmin)