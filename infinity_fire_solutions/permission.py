from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import AuthenticationFailed
from django.urls import reverse
from django.shortcuts import redirect
from django.apps import apps
from django.http import HttpResponseRedirect
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from authentication.models import *


class CustomAuthenticationMixin:
    """
    Mixin to handle authentication based on request format.

    For HTML requests, it allows unauthenticated access and redirects to the login page if needed.
    For API requests, it attempts TokenAuthentication and raises an AuthenticationFailed exception
    if the token is missing or invalid.
    """

    def get_authentication_classes(self):
        """
        Get the authentication classes based on the request format.

        If the request format is HTML, it returns [SessionAuthentication].
        For other formats (API requests), it returns [TokenAuthentication].
        """
        if self.request.accepted_renderer.format == 'html':
            return [SessionAuthentication]
        else:
            return [TokenAuthentication]


    def get_permission_classes(self):
        """
        Get the permission classes based on the request format.

        If the request format is HTML, it returns [AllowAny].
        For other formats (API requests), it returns [IsAuthenticated].
        """
        if self.request.accepted_renderer.format == 'html':
            return [AllowAny]
        else:
            return [IsAuthenticated]
        
        
    def handle_unauthenticated(self):
        """
        Handle unauthenticated access based on the request format.

        For HTML requests, it redirects to the login page if the user is not authenticated.
        For API requests, it attempts TokenAuthentication and raises an AuthenticationFailed
        exception if the token is missing or invalid.
        """
        auth_classes = self.get_authentication_classes()

        for auth_class in auth_classes:
            auth_tuple = auth_class().authenticate(self.request)
            if auth_tuple:
                self.request.user, _ = auth_tuple
                return self.request.user
        
        if self.request.accepted_renderer.format == 'html':
            login_url = reverse('login')
            redirect_url = self.request.path
            return redirect(f'{login_url}?next={redirect_url}')
        else:
            raise AuthenticationFailed("Authentication credentials were not provided.")
        

def get_user_module_permissions(user, module_name):
    """
    Get the module permissions for a specific user.

    Args:
        user (User): The user for whom permissions are to be retrieved.
        module_name (str): The name of the module for which permissions are required.

    Returns:
        dict: A dictionary containing the user's permissions for each role in the module.
              The keys are role names, and the values are dictionaries with the following keys:
              - 'can_list_data': Permission to list data (either "yes" or "none").
              - 'can_create_data': Permission to create data (either True or "none").
              - 'can_change_data': Permission to change data (either "yes" or "none").
              - 'can_delete_data': Permission to delete data (either "yes" or "none").
    """
    user_permissions = {}

    for role in user.roles.all():
        permission = UserRolePermission.objects.filter(role=role, module=module_name).first()
        if permission:
            user_permissions[role.name] = {
                'can_list_data': permission.can_list_data.lower(),
                'can_create_data': permission.can_create_data,
                'can_change_data': permission.can_change_data.lower(),
                'can_delete_data': permission.can_delete_data.lower(),
            }
        else:
            user_permissions[role.name] = {
                'can_list_data': "none",
                'can_create_data': "none",
                'can_change_data': "none",
                'can_delete_data': "none",
            }

    return user_permissions

class HasListDataPermission(BasePermission):
    """
    Permission class to check if the user has permission to list data for a specific module.

    Args:
        module_name (str): The name of the module for which list data permission is required.
    """
    
    def __init__(self, module_name):
        self.module_name = module_name

    def has_permission(self, request, view):
        user = request.user
        user_permissions = get_user_module_permissions(user, self.module_name)

        for permission in user_permissions.values():
            if permission['can_list_data'] != "none":
                return permission['can_list_data']

        # If no permission is found, raise PermissionDenied
        raise PermissionDenied()

class HasCreateDataPermission(BasePermission):
    def __init__(self, module_name):
        self.module_name = module_name

    def has_permission(self, request, view):
        user = request.user
        user_permissions = get_user_module_permissions(user, self.module_name)

        for permission in user_permissions.values():
            if permission['can_create_data'] != "none":
                return permission['can_create_data']

        # If no permission is found, raise PermissionDenied
        raise PermissionDenied()

class HasUpdateDataPermission(BasePermission):
    def __init__(self, module_name):
        self.module_name = module_name

    def has_permission(self, request, view):
        user = request.user
        user_permissions = get_user_module_permissions(user, self.module_name)

        for permission in user_permissions.values():
            if permission['can_change_data'] != "none":
                return permission['can_change_data']

        # If no permission is found, raise PermissionDenied
        raise PermissionDenied()

class HasDeleteDataPermission(BasePermission):
    def __init__(self, module_name):
        self.module_name = module_name

    def has_permission(self, request, view):
        user = request.user
        user_permissions = get_user_module_permissions(user, self.module_name)

        for permission in user_permissions.values():
            if permission['can_delete_data'] != "none":
                return permission['can_delete_data']

        # If no permission is found, raise PermissionDenied
        raise PermissionDenied()

class AuthenticationPermissionMixin:
    """
    Mixin for handling authentication and permission checks.
    """
    
    def handle_unauthenticated(self):
        """
        Handle unauthenticated access.

        Returns:
            HttpResponseRedirect: Redirects to the login page if the user is not authenticated.
            None: If the user is authenticated.
        """
        if not self.request.user.is_authenticated:
            return HttpResponseRedirect("/login/?next=%s" % self.request.path)

    def handle_authentication(self):
        """
        Check authentication and handle unauthenticated access.

        Raises:
            AuthenticationFailed: If authentication credentials were not provided.
        """
        authenticated_user = self.handle_unauthenticated()
        
        if isinstance(authenticated_user, HttpResponseRedirect):
            # If the user is not authenticated and a redirect response is received
            # (for HTML renderer), return the redirect response as it is.
            return authenticated_user

        if not authenticated_user:
            raise AuthenticationFailed("Authentication credentials were not provided")

    
def get_generic_queryset(request, module_name, app_label, data_access_value ):
    """
    Get the queryset for listing items based on the provided module name.

    Args:
        request (HttpRequest): The request object.
        module_name (str): The name of the module for which the queryset is needed.
        model (Model): The model class for which the queryset is needed.
        user_id_field (str): The name of the field representing the user ID in the model (default is "user_id").
        assigned_to_field (str): The name of the field representing the assigned_to field in the model (default is "assigned_to").

    Returns:
        QuerySet: A queryset of items filtered based on the authenticated user's ID.
    """
    # Get the permission value ("self", "all", or None)
    model = apps.get_model(app_label=app_label, model_name=module_name)
    if data_access_value == "self":
        # Filter based on the user's ID and assigned_to field
        
        queryset = model.objects.filter(user_id=request.user).distinct().order_by('-created_at')
    elif data_access_value == "all":
        # Return all data
        print("fjjs")
        queryset = model.objects.all().order_by('-created_at')
    else:
        queryset = model.objects.none()
    return queryset