from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserRole,UserRolePermission
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from .models import InfinityLogs
from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter,DropdownFilter


class UserRolePermissionInline(admin.TabularInline):
    """
    Inline representation of UserRolePermission model for the UserRole model.
    """
    model = UserRolePermission
    extra = 0  # The number of empty forms to display for adding new UserRolePermission instances.
    # Add any other customizations you want for the inline form.

class UserRoleAdmin(admin.ModelAdmin):
    """
    Customizing the admin interface for the UserRole model.
    """
    list_display = ('name', 'created_at','updated_at')
    list_filter = ('name',)
    search_fields = ('name', 'description')
    inlines = [UserRolePermissionInline, ]  # Add the inline here.
    # Add any other customizations you want for the admin interface.


    
class CustomUserAdmin(UserAdmin):
    """
    Customizing the admin interface for the User model.
    """
    list_display = ('email', 'first_name', 'last_name', 'roles', 'is_active','last_login')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name',)}),
        ('Address', {'fields': ('town', 'county','country','post_code','created_by')}),
        ('Permissions', {'fields': ('is_employee', 'is_active', 'is_staff', 'is_superuser', 'roles','enforce_password_change', 'groups')}),

    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'roles', 'is_employee', 'is_active', 'is_staff'),
        }),
    )
    autocomplete_fields = ['roles',]

from admin_auto_filters.filters import AutocompleteFilter
class UserFilter(AutocompleteFilter):
    title = 'user_role' # display title
    field_name = 'user_role' # name of the foreign key field
 
class InfinityLogsAdmin(admin.ModelAdmin):
    list_display = ('module', 'action_type', 'user_role', 'outcome', 'status_code', 'ip_address', 'username', 'timestamp')
    search_fields = ('ip_address',)  # Add 'username' to search fields
    search_help_text = 'search by: IP Address' # Update search help text
    list_filter = (('module',DropdownFilter),
                   ('action_type',DropdownFilter),
                   ('user_role',DropdownFilter),
                   ('outcome',DropdownFilter),
                   ('username',DropdownFilter),
                   ('timestamp',DropdownFilter),                      
    )
    # autocomplete_fields=['']
    readonly_fields = ('timestamp',)
    list_per_page = 20


 
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        # Disable the ability to change existing ContactType instances
        return False
    def has_delete_permission(self, request, obj=None):
        # Disable the ability to delete existing ContactType instances
        return False

admin.site.register(User, CustomUserAdmin)
admin.site.register(InfinityLogs,InfinityLogsAdmin)
admin.site.register(UserRole, UserRoleAdmin)
# admin.site.register(UserRolePermission)
# admin.site.unregister(Group)
