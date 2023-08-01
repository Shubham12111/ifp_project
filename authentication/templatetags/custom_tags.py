from django import template
from infinity_fire_solutions.permission import get_user_module_permissions

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
            return True
    return False