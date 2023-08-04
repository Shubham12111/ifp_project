# middleware.py

from django.urls import reverse
from django.shortcuts import redirect
from django.contrib.auth import logout

class CheckAdminUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith('/admin/'):
            if request.user.is_authenticated and request.user.is_superuser:
                # If the user is authenticated and is a superuser, log them out and redirect to the login page.
                logout(request)
                return redirect('login')
            
        else:
            if request.path.startswith('/admin/'):
                if request.user.is_authenticated and not request.user.is_superuser:
                    # If the user is authenticated and is a superuser, log them out and redirect to the login page.
                    logout(request)
                
        response = self.get_response(request)
        return response