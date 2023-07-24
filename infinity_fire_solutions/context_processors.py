# context_processors.py'
from common_app.models import MenuItem
from django.urls import reverse, resolve

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

def has_group_view_permission(user, required_permissions):
    """
    Checks if the user has the required group permissions to view a menu item.

    Args:
        user (User): The user object to check permissions for.
        required_permissions (list): List of required permissions for the menu item.

    Returns:
        bool: True if the user has any of the required permissions, False otherwise.
    """
    user_groups = user.groups.all()
    for group in user_groups:
        required_permissions = required_permissions.rstrip('s')
        if f'{required_permissions}' in group.permissions.values_list('codename', flat=True):
            return True
    return False


def generate_menu(request, menu_items):
    """
    Recursively generates a menu data structure based on the provided menu items.

    Args:
        request (HttpRequest): The request object containing user information.
        menu_items (list): A list of menu items to be included in the menu.

    Returns:
        list: A menu data structure containing the menu items that the user can access.
    """
    user = request.user
    menu_data = []

    for item in menu_items:
        # Check if the menu item has 'permission_required' key and the user has the required permission
        required_permissions = f"view_{item.name.lower()}"
        if item.permission_required and not has_group_view_permission(user, required_permissions):
            continue
            
        menu_item = {
            'url': item.url,
            'name': item.name,
            'submenu': None,
            'icon': item.icon
        }

         # Check for submenus of the current item
        submenu_items = MenuItem.objects.filter(parent=item, permissions__in=request.user.groups.all())
        
        if submenu_items.exists():
            # Generate submenus recursively
            menu_item['submenu'] = generate_menu(request, submenu_items)

        menu_data.append(menu_item)

    return menu_data

def custom_menu(request):
    """
    Context processor for generating a custom menu data structure.
    """
    user = request.user
    allowed_menu_items = MenuItem.objects.filter(permissions__in = user.groups.all(), parent=None).distinct().order_by('order')
    
    # Generate the final menu data structure using the generate_menu function
    menu_data = generate_menu(request, allowed_menu_items)
    
    return {'menu_items': menu_data}
