from django import template
from infinity_fire_solutions.permission import get_user_module_permissions
from django.urls import resolve, Resolver404
from common_app.models import MenuItem
import re

register = template.Library()

@register.filter
def has_add_permission(user, module_name):
    """
    Custom template filter to check if the user has the 'add' permission for a specific module.

    Args:
        user (User): The user for whom permissions are to be checked.
        module_name (str): The name of the module for which 'add' permission is required.

    Returns:
        bool: True if the user has the 'add' permission for the specified module, False otherwise.
    """
    user_permissions = get_user_module_permissions(user, module_name)
    for permission in user_permissions.values():
        if permission['can_create_data'] != False:
            return permission['can_create_data']


@register.filter
def has_update_permission(user, module_name):
    """
    Custom template filter to check if the user has the 'update' permission for a specific module.

    Args:
        user (User): The user for whom permissions are to be checked.
        module_name (str): The name of the module for which 'update' permission is required.

    Returns:
        bool: True if the user has the 'update' permission for the specified module, False otherwise.
    """
    user_permissions = get_user_module_permissions(user, module_name)
    for permission in user_permissions.values():
        if permission['can_change_data'] != "none":
            if permission['can_change_data'] == "all":
                return permission['can_change_data']
            else:
                return True
    return False

@register.filter
def has_delete_permission(user, module_name):
    """
    Custom template filter to check if the user has the 'delete' permission for a specific module.

    Args:
        user (User): The user for whom permissions are to be checked.
        module_name (str): The name of the module for which 'delete' permission is required.

    Returns:
        bool: True if the user has the 'delete' permission for the specified module, False otherwise.
    """
    user_permissions = get_user_module_permissions(user, module_name)
    for permission in user_permissions.values():
        if permission['can_delete_data'] != "none":
            if permission['can_delete_data'] == "all":
                return permission['can_delete_data']
            else:
                return True
    return False


@register.filter
def has_view_permission(user, module_name):
    """
    Custom template filter to check if the user has the 'view' permission for a specific module.

    Args:
        user (User): The user for whom permissions are to be checked.
        module_name (str): The name of the module for which 'view' permission is required.

    Returns:
        bool: True if the user has the 'view' permission for the specified module, False otherwise.
    """
    user_permissions = get_user_module_permissions(user, module_name)
    for permission in user_permissions.values():
        if permission['can_view_data'] != "none":
            if permission['can_view_data'] == "all":
                return permission['can_view_data']
            else:
                return True
    return False

@register.filter
def get_active_menu(current_path):
    """
    Determines the active menu based on the current URL path.
    
    Args:
        current_path (str): The current URL path.
        
    Returns:
        str: The active menu name or None if no active menu found.
    """
    allowed_menu_items = MenuItem.objects.filter(parent=None).distinct().order_by('order')
    current_url = current_path
    active_menu = None
    pattern = r"s$" 
    # Use regular expression to extract the first segment (part between slashes)
    match = re.match(r'^/([^/]+)/', current_url)
    if match:
        first_segment = match.group(1)
    else:
        first_segment = None
    first_segment = re.sub(pattern, "", first_segment.replace(" ", "_")).lower()
    for item in allowed_menu_items:
        # Convert menu name to lowercase and replace spaces with underscores
        # Remove trailing "s" from plural menu names
        menu_name = re.sub(pattern, "", item.name.replace(" ", "_")).lower()
        # Check if the menu name is in the first segment of the URL
        if menu_name in first_segment:
            active_menu = menu_name
            return active_menu
    
    return active_menu


@register.filter
def capitalize_fra(value):
    # Split the value by "FRA"
    parts = value.split(" ")
    return parts[0].upper() + " "+ parts[1]