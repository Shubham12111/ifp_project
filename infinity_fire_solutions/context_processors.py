# context_processors.py
from django.conf import settings
from infinity_fire_solutions.menu_list import MENU_ITEMS

def find_breadcrumb(menu_items, current_path):
    """
    Recursively searches for the matching breadcrumb for the current URL.
    Returns the breadcrumb item or None if no match is found.
    """
    for item in menu_items:
        if current_path.startswith(item['url']):
            return item

        if 'submenu' in item:
            subitem = find_breadcrumb(item['submenu'], current_path)
            if subitem:
                return subitem

    return None

def breadcrumbs(request):
    """
    Context processor for generating breadcrumbs data based on the current URL.
    """
    current_path = request.path
    include_paths = ['/add/', '/edit/', '/auth/profile/']

    breadcrumbs_data = []
    
    paths_dict = {
        '/add/': 'Add',
        '/edit/': 'Edit',
        '/auth/profile/': 'Profile',
        }
    
    # Find the matching breadcrumb for the current URL
    menu_items = sorted(MENU_ITEMS, key=lambda item: item.get('order', float('inf')))
    
    breadcrumb = find_breadcrumb(menu_items, current_path)

    try:
        if breadcrumb and breadcrumb['url'] == current_path:
            breadcrumbs_data.append(breadcrumb)
        elif current_path in include_paths:
            breadcrumbs_data.append({'url': current_path, 'name': paths_dict.get(current_path)})
        
        else:
            breadcrumbs_data.append({'url': current_path, 'name': current_path})
    except KeyError:
        pass
    
    return {'breadcrumbs_data': breadcrumbs_data}


def generate_menu(menu_items):
    """
    Recursively generates a menu data structure based on the provided menu items.
    Returns the menu data.
    """
    menu_items = sorted(menu_items, key=lambda item: item.get('order', float('inf')))

    menu_data = []

    for item in menu_items:
        menu_item = {
            'url': item.get('url'),
            'name': item.get('name'),
            'submenu': None,
            'icon': item.get('icon')
        }

        if 'submenu' in item:
            submenu_items = generate_menu(item['submenu'])
            if submenu_items:
                menu_item['submenu'] = submenu_items

        menu_data.append(menu_item)

    return menu_data


def custom_menu(request):
    """
    Context processor for generating a custom menu data structure.
    """
    menu_items = generate_menu(MENU_ITEMS)
    return {'menu_items': menu_items}
