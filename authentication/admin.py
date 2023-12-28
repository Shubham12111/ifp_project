from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserRole,UserRolePermission
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from .models import InfinityLogs



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
    list_display = ('email', 'first_name', 'last_name','is_active','last_login')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name',)}),
        ('Address', {'fields': ('town', 'county','country','post_code','created_by')}),
        ('Permissions', {'fields': ('is_active','roles','enforce_password_change')}),

    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'roles'),
        }),
    )
    autocomplete_fields = ['roles',]

 

class InfinityLogsAdmin(admin.ModelAdmin):
    list_display = ('api', 'access_type', 'ip_address', 'timestamp')
    search_fields = ('api', 'ip_address', 'username')  # Add any other fields you want to search on
    list_filter = ('access_type', 'outcome', 'module', 'action_type', 'method')
    readonly_fields = ('timestamp',)  # You may add other fields as needed

admin.site.register(User, CustomUserAdmin)
admin.site.register(InfinityLogs)
admin.site.register(UserRole, UserRoleAdmin)
admin.site.register(UserRolePermission)
admin.site.unregister(Group)