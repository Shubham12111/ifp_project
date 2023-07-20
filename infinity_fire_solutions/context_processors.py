# context_processors.py
from django.conf import settings
from infinity_fire_solutions.menu_list import MENU_ITEMS
from django.urls import reverse
import re 

from django.urls import resolve

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



# def find_breadcrumb(menu_items, current_path):
#     """
#     Recursively searches for the matching breadcrumb for the current URL.
#     Returns the breadcrumb item or None if no match is found.
#     """
#     for item in menu_items:
#         if current_path.startswith(item['url']):
#             return item

#         if 'submenu' in item:
#             subitem = find_breadcrumb(item['submenu'], current_path)
#             if subitem:
#                 return subitem

#     return None

# def get_breadcrumb_name(segment):
#     """
#     Function to get the breadcrumb name based on a URL segment.
#     You can implement custom logic here to retrieve the title based on the URL segment.
#     """
#     # Example implementation: You can replace this with your own logic to get the title.
#     # For simplicity, we check if the segment is a numeric ID. If it is, we return None to exclude it from breadcrumbs.
#     if re.match(r'^\d+$', segment):
#         return None
#     else:
#         return segment.capitalize()

# def breadcrumbs(request):
#     """
#     Context processor for generating breadcrumbs data based on the current URL.
#     """
#     breadcrumbs_data = []
#     current_path = request.path
#     path_segments = current_path.strip('/').split('/')

#     for idx, segment in enumerate(path_segments):
#         url = '/'.join(path_segments[:idx+1])
#         name = get_breadcrumb_name(segment)

#         if name:
#             breadcrumbs_data.append({'url': reverse('view_name', args=[url]), 'name': name})

#     return {'breadcrumbs_data': breadcrumbs_data}


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
