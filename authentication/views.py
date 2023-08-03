from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import login
from django.contrib.auth import logout
from .serializers import LoginSerializer, SignupSerializer, ForgotPasswordSerializer, VerifyOTPSerializer, UserProfileSerializer, ChangePasswordSerializer
from .models import User,UserRole

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
        if self.request.user.is_authenticated:
            return redirect(reverse('dashboard'))
        
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
            if user.is_superuser:
                messages.error(request, 'Login failed. The credentials provided are incorrect. Please verify your login information and try again.')
                return self.render_html_response(serializer)
            # Render the HTML template for successful login
            login(request, user)
            #messages.success(request, 'Congratulations! You have successfully logged in to your account. Enjoy your experience!')
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
        if self.request.user.is_authenticated:
            return redirect(reverse('dashboard'))
        
        serializer = self.serializer_class()
        # Render the HTML template for login page
        return self.render_html_response(serializer)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            # Check if the checkbox is checked
            agreed_to_terms = request.data.get('agreed_to_terms', False)
            if not agreed_to_terms:
                if request.accepted_renderer.format == 'html':
                    return Response(
                        {'serializer': serializer, 'error_message': 'You must agree to the Terms and Conditions.'},
                        template_name=self.template_name,
                        status=400,
                    )
                else:
                    return Response({'error': 'You must agree to the Terms and Conditions.'}, status=400)


            user = serializer.save()
            user.set_password(serializer.validated_data["password"])
            user_roles = UserRole.objects.filter(name="Contractor").first()
            if user_roles:
                user.roles.add(user_roles)  # Assuming user has a ManyToManyField for roles
            user.save()
            
            # Redirect or respond with success message as needed
            messages.success(request, "User registered successfully. Please login here.")
            return redirect(reverse('login'))
        
        else:
            # Render the HTML template with invalid serializer data
            return self.render_html_response(serializer)
        
class LogoutView(APIView):
    """
    View for user logout.
    """
    def get(self, request):
        """
        Handle GET request for user logout.
        """
        # Log the user out
        if self.request.user.is_authenticated:
            logout(request)
        
        # Redirect to a specific page after logout (you can change 'login' to the desired page name)
        return redirect(reverse('login'))


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
        if self.request.user.is_authenticated:
            return redirect(reverse('dashboard'))
        
        serializer = self.serializer_class()
        # Render the HTML template for login page
        return self.render_html_response(serializer)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data.get('email')
        
            try:
                user = User.objects.get(email=email)
                # Email exists in the system, proceed with sending the OTP
                # Render the HTML template with invalid serializer data
                messages.info(request, f"Please note that an OTP (One-Time Password) has been sent to the email address {email}.")
                return redirect(reverse('verify_otp'))

            except User.DoesNotExist:
                # Email does not exist in the system
                messages.error(request, f"We apologize, but it seems that the email {email} is not associated with our records.")
                return self.render_html_response(serializer)
            

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
        if self.request.user.is_authenticated:
            return redirect(reverse('dashboard'))
        
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

class ProfileView(APIView):
    
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    serializer_class = UserProfileSerializer
    template_name = "profile.html"

    
    def render_html_response(self, serializer):
        """
        Render HTML response using the provided serializer and template name.
        """
        return Response({'serializer': serializer}, template_name=self.template_name)

    def get(self, request):
        """
        Handle GET request for login page.
        """
        # return redirect(reverse('dashboard'))
        

        serializer = self.serializer_class(instance=request.user)
        # Render the HTML template for login page
        return self.render_html_response(serializer)
    
    def post(self, request):
        data = request.data.copy()  # Create a mutable copy of request.data
        data.update({'email': request.user.email})  # Update the copy with the new email value

        serializer = self.serializer_class(data=data, instance=request.user)
        if serializer.is_valid():
            serializer.save()
            messages.success(request, f"Profile Updated: Your changes have been saved successfully! Thank you for keeping your information up to date")
            return redirect(reverse('profile'))

        else:
            return self.render_html_response(serializer)


class ChangePasswordView(APIView):
    
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    serializer_class = ChangePasswordSerializer
    template_name = "change_password.html"

    
    def render_html_response(self, serializer):
        """
        Render HTML response using the provided serializer and template name.
        """
        return Response({'serializer': serializer}, template_name=self.template_name)

    def get(self, request):
        """
        Handle GET request for login page.
        """
        # return redirect(reverse('dashboard'))
        
        serializer = self.serializer_class()
        # Render the HTML template for login page

        return self.render_html_response(serializer)

    def post(self, request):
        data = request.data
        serializer = self.serializer_class(data=data, instance=request.user, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            messages.success(request, f"Password updated successfully. Please use your new password for future logins.")
            return redirect(reverse('profile'))

        else:
            return self.render_html_response(serializer)

