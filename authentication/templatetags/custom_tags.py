from django import template
from infinity_fire_solutions.permission import get_user_module_permissions

register = template.Library()

@register.filter
def has_permission(user, module_name):
    # Implement your logic to check if the user has the specified permission
    user_permissions = get_user_module_permissions(user,module_name)
    if user_permissions:
        return True
    else:
        return False