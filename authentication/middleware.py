
# middleware.py
from django.urls import reverse
from django.shortcuts import redirect
from django.contrib.auth import logout
from django.urls import resolve
from django.http import HttpResponse
from authentication.signals import api_request_logged
from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.dispatch import receiver


class CheckAdminUserMiddleware:
    """
    Middleware class for checking and enforcing superuser access to the admin panel.

    This middleware ensures that only superusers can access the Django admin panel.
    If a non-superuser attempts to access the admin panel, they are logged out and redirected.

    Args:
        get_response (function): The next middleware or view function in the request-response chain.

    Usage example:
        # Add this middleware to your project's settings.py
        MIDDLEWARE = [
            ...
            'your_app.middleware.CheckAdminUserMiddleware',
            ...
        ]
    """

    def __init__(self, get_response):
        """
        Initialize the middleware.

        Args:
            get_response (function): The next middleware or view function in the request-response chain.
        """
        self.get_response = get_response

    def __call__(self, request):
        """
        Process incoming requests.

        This method is called for each incoming request and enforces superuser access to the admin panel.

        Args:
            request (HttpRequest): The incoming HTTP request.

        Returns:
            HttpResponse: The response object for the request.
        """
        if not request.path.startswith('/admin/'):
            if request.user.is_authenticated and request.user.is_superuser:
                # If the user is authenticated and is a superuser, log them out and redirect to the login page.
                logout(request)
                return redirect('login')
        else:
            if request.path.startswith('/admin/'):
                if request.user.is_authenticated and not request.user.is_superuser:
                    # If the user is authenticated and is not a superuser, log them out.
                    logout(request)

        response = self.get_response(request)
        return response

class ForcePasswordChangeBackend:
    """
    Middleware class for enforcing password change for certain users.

    This middleware checks whether the user should be forced to change their password
    and redirects them to the password change page if necessary.

    Args:
        get_response (function): The next middleware or view function in the request-response chain.

    Usage example:
        # Add this middleware to your project's settings.py
        MIDDLEWARE = [
            ...
            'your_app.middleware.ForcePasswordChangeBackend',
            ...
        ]
    """

    def __init__(self, get_response):
        """
        Initialize the middleware.

        Args:
            get_response (function): The next middleware or view function in the request-response chain.
        """
        self.get_response = get_response

    def __call__(self, request):
        """
        Process incoming requests.

        This method is called for each incoming request and decides whether the user
        should be redirected to the password change page.

        Args:
            request (HttpRequest): The incoming HTTP request.

        Returns:
            HttpResponse: The response object for the request.
        """
        # Define a list of URL paths that should bypass password change enforcement
        if not request.path.startswith('/admin/'):
            allowed_paths = [
                reverse('login'),
                reverse('signup'),
                reverse('forgot_password')
            ] 

            if request.user.is_authenticated:
                if request.path in allowed_paths:
                    logout(request)
                elif not request.user.enforce_password_change and request.path != reverse('enforce_password_change'):
                    return redirect('enforce_password_change')

        response = self.get_response(request)
        return response

class SimpleAPILoggerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Continue with the original request processing
        request_data = request.body if request.body else ''
        response = self.get_response(request)

        # Check if the request is in the 'admin' namespace
        namespace = resolve(request.path_info).namespace

        if namespace == 'admin':
            return response

        api_request_logged.send(
            sender=self.__class__,
            request_data=request_data,
            request=request,
            response=response,
        )

        # Add the function call to capture request and response payload
        # self.log_request_and_response(request_data, response)

        return response
    

