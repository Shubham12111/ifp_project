from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from .serializers import LoginSerializer, SignupSerializer, ForgotPasswordSerializer, VerifyOTPSerializer
from infinity_fire_solutions.response_schemas import create_api_response

class LoginView(APIView):
    """
    API view for user login.
    """
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    serializer_class = LoginSerializer
    template_name = "login.html"

    def render_html_response(self, serializer):
        """
        Render HTML response using the provided serializer and template name.
        """
        return Response({'serializer': serializer}, template_name=self.template_name)

    def get(self, request):
        """
        Handle GET request for login page.
        """
        serializer = self.serializer_class()

        # Render the HTML template for login page
        return self.render_html_response(serializer)

    def post(self, request):
        """
        Handle POST request for user login.
        """
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            # Validating the serializer data

            email = serializer.validated_data.get('email')
            password = serializer.validated_data.get('password')
            user = authenticate(request=request, email=email, password=password)

            if not user:
                # User authentication failed
                # Render the HTML template with error message
                messages.error(request, 'Login failed. The credentials provided are incorrect. Please verify your login information and try again.')
                return self.render_html_response(serializer)

            # Render the HTML template for successful login
            messages.success(request, 'Login failed. The credentials provided are incorrect. Please verify your login information and try again.')
            return redirect(reverse('dashboard'))

        else:
            # Render the HTML template with invalid serializer data
            return self.render_html_response(serializer)


class SignupView(APIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    serializer_class = SignupSerializer
    template_name = "signup.html"

    
    def render_html_response(self, serializer):
        """
        Render HTML response using the provided serializer and template name.
        """
        return Response({'serializer': serializer}, template_name=self.template_name)

    def get(self, request):
        """
        Handle GET request for login page.
        """
        serializer = self.serializer_class()

        # Render the HTML template for login page
        return self.render_html_response(serializer)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            # Validating the serializer data
            name = serializer.validated_data.get('name')
            email = serializer.validated_data.get('email')
            password = serializer.validated_data.get('password')

            register_data = {
                'name':  name,
                'email': email,
                'password': password
            }

            # Create a new user with the validated serializer data
            user_serializer = LoginSerializer(data=register_data)
            if user_serializer.is_valid():
                try:
                    user = user_serializer.save()
                except Exception as e:
                    error = str(e)
                    messages.error(request, f'{error}')

                    # Render the HTML template for successful signup
                    return self.render_html_response(serializer)
                        
                # Additional logic after user signup (e.g., sending email, generating tokens, etc.)
                messages.success(request, 'User signed up successfully.')

                # Render the HTML template for successful signup
                return redirect('/auth/login/')
            else:
                messages.error(request, 'User Registeration Failed.')
                return self.render_html_response(serializer)

        else:
            # Render the HTML template with invalid serializer data
            return self.render_html_response(serializer)


class ForgotPasswordView(APIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    serializer_class = ForgotPasswordSerializer
    template_name = "forgot.html"

    
    def render_html_response(self, serializer):
        """
        Render HTML response using the provided serializer and template name.
        """
        return Response({'serializer': serializer}, template_name=self.template_name)

    def get(self, request):
        """
        Handle GET request for login page.
        """
        serializer = self.serializer_class()

        # Render the HTML template for login page
        return self.render_html_response(serializer)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            # Render the HTML template with invalid serializer data
            messages.info(request, "OTP will be sent to your email, if you're registered.")
            return redirect('/auth/verify/')

        else:
            # Invalid serializer data
            # Render the HTML template with invalid serializer data
            return self.render_html_response(serializer)


class VerifyOTPView(APIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    serializer_class = VerifyOTPSerializer
    template_name = "verify_otp.html"

    
    def render_html_response(self, serializer):
        """
        Render HTML response using the provided serializer and template name.
        """
        return Response({'serializer': serializer}, template_name=self.template_name)

    def get(self, request):
        """
        Handle GET request for login page.
        """
        serializer = self.serializer_class()

        # Render the HTML template for login page
        return self.render_html_response(serializer)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            # Render the HTML template with invalid serializer data
            messages.warning(request, "Not Implemented yet")
            return self.render_html_response(serializer)

        else:
            # Invalid serializer data
            # Render the HTML template with invalid serializer data
            return self.render_html_response(serializer)
