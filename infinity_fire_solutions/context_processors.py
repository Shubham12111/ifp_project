# context_processors.py'
from common_app.models import MenuItem
from django.urls import reverse, resolve
from infinity_fire_solutions.permission import get_user_module_permissions

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

    # Capitalize non-numeric segments and add to breadcrumbs_data
    for segment in path_segments:
        if segment.isdigit():
            continue
        name = underscore_to_space(segment)
        breadcrumbs_data.append({'name': name.capitalize()})

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
    user_permissions = get_user_module_permissions(user, module_name)
    # Check both "can list data" and "can create data" permissions
    for permission in user_permissions.values():
        if permission.get('can_create_data') != 'none' or permission.get('can_list_data') != 'none':
            return True
    
    return False  # If no appropriate permission found, return False


def generate_menu(request, menu_items):
    menu_data = []

    for item in menu_items:
        if item.name.lower() == 'dashboard':
            # Add the dashboard menu item, visible to all users
            menu_item = {
                'url': item.url,
                'name': item.name,
                'submenu': None,
                'icon': item.icon
            }
            menu_data.append(menu_item)
        elif has_view_permission(request.user, item.name):
            # Add other menu items with view permission
            menu_item = {
                'url': item.url,
                'name': item.name,
                'submenu': None,
                'icon': item.icon
            }
            
             # Check for submenus of the current item
            submenu_items = MenuItem.objects.filter(parent=item)
        
            if submenu_items.exists():
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
            
    return {'menu_items': menu_data}
