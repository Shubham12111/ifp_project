from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import AuthenticationFailed
from django.urls import reverse
from django.shortcuts import redirect


class CustomAuthenticationMixin:
    """
    Mixin to handle authentication based on request format.

    For HTML requests, it allows unauthenticated access and redirects to the login page if needed.
    For API requests, it attempts TokenAuthentication and raises an AuthenticationFailed exception
    if the token is missing or invalid.
    """

    def get_authentication_classes(self):
        """
        Get the authentication classes based on the request format.

        If the request format is HTML, it returns [SessionAuthentication].
        For other formats (API requests), it returns [TokenAuthentication].
        """
        if self.request.accepted_renderer.format == 'html':
            return [SessionAuthentication]
        else:
            return [TokenAuthentication]


    def get_permission_classes(self):
        """
        Get the permission classes based on the request format.

        If the request format is HTML, it returns [AllowAny].
        For other formats (API requests), it returns [IsAuthenticated].
        """
        if self.request.accepted_renderer.format == 'html':
            return [AllowAny]
        else:
            return [IsAuthenticated]
        
        
    def handle_unauthenticated(self):
        """
        Handle unauthenticated access based on the request format.

        For HTML requests, it redirects to the login page if the user is not authenticated.
        For API requests, it attempts TokenAuthentication and raises an AuthenticationFailed
        exception if the token is missing or invalid.
        """
        auth_classes = self.get_authentication_classes()

        for auth_class in auth_classes:
            auth_tuple = auth_class().authenticate(self.request)
            if auth_tuple:
                self.request.user, _ = auth_tuple
                return self.request.user
        
        if self.request.accepted_renderer.format == 'html':
            login_url = reverse('login')
            redirect_url = self.request.path
            return redirect(f'{login_url}?next={redirect_url}')
        else:
            raise AuthenticationFailed("Authentication credentials were not provided.")