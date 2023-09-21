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
from django.db.models import Q


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
    if user.roles:
        role = user.roles
        permission = UserRolePermission.objects.filter(role=role, module=module_name).first()
        if permission:
            user_permissions[role.name] = {
                'can_list_data': permission.can_list_data.lower(),
                'can_create_data': permission.can_create_data,
                'can_change_data': permission.can_change_data.lower(),
                'can_delete_data': permission.can_delete_data.lower(),
                'can_view_data': permission.can_view_data.lower(),
            }
        else:
            user_permissions[role.name] = {
                'can_list_data': "none",
                'can_create_data': "none",
                'can_change_data': "none",
                'can_delete_data': "none",
                'can_view_data': "none",
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
    """
    Custom permission class to check if a user has permission to create data in a specific module.

    Args:
        module_name (str): The name of the module for which permission is checked.

    Attributes:
        module_name (str): The name of the module for which permission is checked.
    """

    def __init__(self, module_name):
        self.module_name = module_name

    def has_permission(self, request, view):
        """
        Check if the user has permission to create data in the specified module.

        Args:
            request (HttpRequest): The HTTP request object.
            view (View): The view requesting the permission check.

        Returns:
            bool: True if the user has permission to create data, False otherwise.

        Raises:
            PermissionDenied: If no permission is found.
        """
        user = request.user
        user_permissions = get_user_module_permissions(user, self.module_name)

        for permission in user_permissions.values():
            if permission['can_create_data'] != False:
                return permission['can_create_data']

        # If no permission is found, raise PermissionDenied
        raise PermissionDenied()

class HasUpdateDataPermission(BasePermission):
    """
    Custom permission class to check if a user has permission to update data in a specific module.

    Args:
        module_name (str): The name of the module for which permission is checked.

    Attributes:
        module_name (str): The name of the module for which permission is checked.
    """
    def __init__(self, module_name):
        self.module_name = module_name

    def has_permission(self, request, view):
        """
        Check if the user has permission to update data in the specified module.

        Args:
            request (HttpRequest): The HTTP request object.
            view (View): The view requesting the permission check.

        Returns:
            bool: True if the user has permission to update data, False otherwise.

        Raises:
            PermissionDenied: If no permission is found.
        """
        user = request.user
        user_permissions = get_user_module_permissions(user, self.module_name)

        for permission in user_permissions.values():
            if permission['can_change_data'] != "none":
                return permission['can_change_data']

        # If no permission is found, raise PermissionDenied
        raise PermissionDenied()

class HasDeleteDataPermission(BasePermission):
    """
    Custom permission class to check if a user has permission to delete data in a specific module.

    Args:
        module_name (str): The name of the module for which permission is checked.

    Attributes:
        module_name (str): The name of the module for which permission is checked.
    """
    def __init__(self, module_name):
        self.module_name = module_name

    def has_permission(self, request, view):
        """
        Check if the user has permission to delete data in the specified module.

        Args:
            request (HttpRequest): The HTTP request object.
            view (View): The view requesting the permission check.

        Returns:
            bool: True if the user has permission to delete data, False otherwise.

        Raises:
            PermissionDenied: If no permission is found.
        """
        user = request.user
        user_permissions = get_user_module_permissions(user, self.module_name)

        for permission in user_permissions.values():
            if permission['can_delete_data'] != "none":
                return permission['can_delete_data']

        # If no permission is found, raise PermissionDenied
        raise PermissionDenied()

class HasViewDataPermission(BasePermission):
    """
    Custom permission class to check if a user has permission to view data in a specific module.

    Args:
        module_name (str): The name of the module for which permission is checked.

    Attributes:
        module_name (str): The name of the module for which permission is checked.
    """
    def __init__(self, module_name):
        self.module_name = module_name

    def has_permission(self, request, view):
        """
        Check if the user has permission to view data in the specified module.

        Args:
            request (HttpRequest): The HTTP request object.
            view (View): The view requesting the permission check.

        Returns:
            bool: True if the user has permission to view data, False otherwise.

        Raises:
            PermissionDenied: If no permission is found.
        """
        user = request.user
        user_permissions = get_user_module_permissions(user, self.module_name)

        for permission in user_permissions.values():
            if permission['can_view_data'] != "none":
                return permission['can_view_data']

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

    
def check_authentication_and_permissions(view_instance,module_name, permission_class, view_type):
    authenticated_user = view_instance.handle_unauthenticated()

    if isinstance(authenticated_user, HttpResponseRedirect):
        return authenticated_user, None

    if not authenticated_user:
        raise AuthenticationFailed("Authentication credentials were not provided")

    view_instance.request.user = authenticated_user
    permission_instance = permission_class(module_name=module_name)

    # Get the data access value (either "self" or "all") based on the view type
    data_access_value = permission_instance.has_permission(view_instance.request, view_type)
    
    return authenticated_user, data_access_value