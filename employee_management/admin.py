from typing import Any
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.http.request import HttpRequest
from employee_management.models import EmployeeUser
# Register your models here.

class EmployeeAdmin(UserAdmin):

    list_display = ('email', 'first_name', 'last_name', 'is_active', 'roles', 'last_login')
    search_fields = ('email', 'first_name', 'last_name')
    search_help_text = 'Search Employee by: Email, First Name, Last Name'
    ordering = ('email',)
    
    list_filter = ('is_active', 'roles')
    
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

    list_per_page = 20

    def get_queryset(self, request):
        """
        Return a QuerySet of all model instances that can be edited by the
        admin site. This is used by changelist_view.
        """
        qs = self.model._default_manager.get_queryset()
        
        # add a filter to check if the user is the employee or not.
        qs = qs.exclude(roles__name="Customer").filter(is_employee=True)

        # TODO: this should be handled by some parameter to the ChangeList.
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs
    
    def save_form(self, request: Any, form: Any, change: Any) -> Any:
        """
        Overrides the save_form method to ensure the instance is marked as an employee.

        Args:
            request (Any): The request object.
            form (Any): The form instance.
            change (Any): Indicates if it's a change to an existing instance.

        Returns:
            Any: The saved instance after modification.
        """
        instance = super().save_form(request, form, change)
        if not instance.is_employee:
            instance.is_employee = True
            instance.save()
        return instance

admin.site.register(EmployeeUser, EmployeeAdmin)