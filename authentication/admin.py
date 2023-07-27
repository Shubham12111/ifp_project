from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserRole,UserRolePermission
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.admin import UserAdmin


class UserRolePermissionInline(admin.TabularInline):
    """
    Inline representation of UserRolePermission model for the UserRole model.
    """
    model = UserRolePermission
    extra = 1  # The number of empty forms to display for adding new UserRolePermission instances.
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
        ('Personal Info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff','groups',)}),

    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'groups','is_staff'),
        }),
    )

admin.site.register(User, CustomUserAdmin)

# Register the models with the custom admin interface.
admin.site.register(UserRole, UserRoleAdmin)
admin.site.register(UserRolePermission)