# context_processors.py'
from common_app.models import MenuItem
from django.urls import reverse, resolve
from infinity_fire_solutions.permission import get_user_module_permissions
import re


def breadcrumbs(request):
    """
    Context processor for generating breadcrumbs data based on the current URL.
    """
    breadcrumbs_data = []
    current_path = request.path
    path_segments = current_path.strip('/').split('/')

    # Helper function to convert underscore-separated words to space-separated words
    def underscore_to_space(word):
        return word.replace('_', ' ')

    # Remove "AUTH" from the segments
    path_segments = [segment for segment in path_segments if segment.upper() != "AUTH"]

    # Combine non-numeric segments and add to breadcrumbs_data
    name = " ".join([underscore_to_space(segment) for segment in path_segments if not segment.isdigit()])
    if name:
        breadcrumbs_data.append({'name': name.capitalize(), 'url': current_path})

    # Add default dashboard breadcrumb
    breadcrumbs_data.insert(0, {'name': 'Dashboard', 'url': '/'})

    return {'breadcrumbs_data': breadcrumbs_data}


def has_view_permission(user, module_name):

    """
    Custom template filter to check if the user has the 'add' permission for a specific module.

    Args:
        user (User): The user for whom permissions are to be checked.
        module_name (str): The name of the module for which 'add' permission is required.

    Returns:
        bool: True if the user has the 'add' permission for the specified module, False otherwise.
    """
    user_permissions = get_user_module_permissions(user, module_name.lower())
    # Check both "can list data" and "can create data" permissions
    for permission in user_permissions.values():
        return permission.get('can_create_data') or permission.get('can_list_data') != 'none'
            
    # If no appropriate permission found, return False
    return False


def generate_menu(request, menu_items):
    menu_data = []

    for item in menu_items:
        pattern = r"s$"
        if not item.permission_required or item.parent:
            # Add the dashboard menu item, visible to all users
            menu_item = {
                'url': item.url,
                'name': item.name,
                'submenu': None,
                'icon': item.icon
            }
            menu_data.append(menu_item)
        
        elif has_view_permission(request.user, re.sub(pattern, "", item.name.replace(" ", "_"))) and not has_view_permission(request.user, re.sub(pattern, "", item.name.replace(" ", "_"))) == 'none':
            # Add other menu items with view permission
            menu_item = {
                'url': item.url,
                'name': item.name,
                'submenu': None,
                'icon': item.icon
            }
            
             # Check for submenus of the current item
            submenu_items = MenuItem.objects.filter(parent=item)
            if submenu_items:
             #Generate submenus recursively
                menu_item['submenu'] = generate_menu(request, submenu_items)

            menu_data.append(menu_item)
            
    return menu_data

def custom_menu(request):
    """
    Context processor for generating a custom menu data structure.
    """
    menu_data = {}
    user = request.user
    if user.is_authenticated:
        if user.roles:
            allowed_menu_items = MenuItem.objects.filter(parent=None).distinct().order_by('order')
            
            # Generate the final menu data structure using the generate_menu function
            menu_data = generate_menu(request, allowed_menu_items)
    print(menu_data) 
    return {'menu_items': menu_data}
