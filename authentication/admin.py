from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserRole,UserRolePermission
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group



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
    list_display = ('email', 'first_name', 'last_name','is_active','last_login')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name',)}),
        ('Address', {'fields': ('town', 'county','country','post_code')}),
        ('Permissions', {'fields': ('is_active','roles',)}),

    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'roles'),
        }),
    )
    autocomplete_fields = ['roles',]

 

admin.site.register(User, CustomUserAdmin)

# Register the models with the custom admin interface.
admin.site.register(UserRole, UserRoleAdmin)
admin.site.register(UserRolePermission)
admin.site.unregister(Group)