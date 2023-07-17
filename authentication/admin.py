from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.admin import UserAdmin



    
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
