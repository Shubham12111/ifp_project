MENU_ITEMS = [
    {'url': '/', 'name': 'Dasboard', 'permission_required':False,'icon': 'fas fa-chart-bar', 'order': 1},
    {
        'url': '/contact/list/',
        'permission_required':True,
        'permissions': ['list_contact'],
        'name': 'Contacts',
        # 'submenu': [
        #     {'url': '/products/category1/', 'name': 'Category 1', 'icon': '<svg>Your SVG Icon Markup Here</svg>'},
        #     {'url': '/products/category2/', 'name': 'Category 2', 'icon': '<svg>Your SVG Icon Markup Here</svg>'},
        # ],
        'icon': 'fas fa-users',
         'order': 2
        
    },
    
     {
        'url': '/todo/list/',
        'name': 'Todo',
        'permission_required':True,
        'permissions': ['list_todo'],
        'icon': 'fas fa-tasks',
        'order': 3
        
    },
]