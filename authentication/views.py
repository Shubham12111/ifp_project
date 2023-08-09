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
from .serializers import *
from .models import User,UserRole
from infinity_fire_solutions.email import *
from infinity_fire_solutions.custom_form_validation import *
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from infinity_fire_solutions.response_schemas import create_api_response, render_html_response
from infinity_fire_solutions.permission import *
from drf_yasg.utils import swagger_auto_schema
from infinity_fire_solutions.utils import docs_schema_response_new

from common_app.models import EmailNotificationTemplate

class LoginView(APIView):
    """
    API view for user login.
    """
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    serializer_class = LoginSerializer
    template_name = "login.html"

    @swagger_auto_schema(auto_schema=None)    
    def get(self, request):
        """
        Handle GET request for login page.
        """
        if self.request.user.is_authenticated:
            return redirect(reverse('dashboard'))
        
        serializer = self.serializer_class()
        # Render the HTML template for login page
        return render_html_response({'serializer': serializer}, self.template_name)

    common_post_response = {
    status.HTTP_200_OK: 
        docs_schema_response_new(
            status_code=status.HTTP_200_OK,
            serializer_class=serializer_class,
            message = "Login successful.",
            )
    }
    
    @swagger_auto_schema(operation_id='Login', responses={**common_post_response})

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

            if not user or user.is_superuser:
                # User authentication failed or is a superuser
                # Render the HTML template with error message

                error_message = 'Login failed. The credentials provided are incorrect. Please verify your login information and try again.'
                messages.error(request, error_message)

                if request.accepted_renderer.format == 'html':
                    # Render the HTML template with error message
                    return render_html_response({'serializer': serializer}, self.template_name)
                else:
                    # Return API response with error message
                    return create_api_response(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        message=error_message
                    )

            else:
                login(request, user)
                # User authentication succeeded
                if request.accepted_renderer.format == 'html':
                    # Render the HTML template for successful login
                    return redirect(reverse('dashboard'))
                else:
                    try:
                        existing_token = Token.objects.get(user=user)
                        # Delete the existing token
                        existing_token.delete()
                    except Token.DoesNotExist:
                        # No existing token found
                        pass

                    # Generate a new token for the user
                    new_token = Token.objects.create(user=user)
                    
                    if new_token:
                        # Return API response with success message and new token

                        return create_api_response(
                            status_code=status.HTTP_200_OK,
                            message="Login successful",
                            data= f'Token {new_token.key}'
                        )
                    else:
                        return create_api_response(
                            status_code=status.HTTP_403_FORBIDDEN,
                            message="Login Failed"
                        )


        else:
            # Serializer data is invalid
            if request.accepted_renderer.format == 'html':
                # Render the HTML template with invalid serializer data
                return render_html_response({'serializer': serializer}, self.template_name)
            else:
                # Return API response with validation errors
                return create_api_response(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="Validation errors",
                    data=serializer.errors
                )


class SignupView(APIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    serializer_class = SignupSerializer
    template_name = "signup.html"

    @swagger_auto_schema(auto_schema=None)
    def get(self, request):
        """
        Handle GET request for signup page.
        """
        if self.request.user.is_authenticated:
            return redirect(reverse('dashboard'))

        serializer = self.serializer_class()

        # Render the HTML template for signup page
        return render_html_response({'serializer': serializer}, self.template_name)

    common_post_response = {
    status.HTTP_200_OK: 
        docs_schema_response_new(
            status_code=status.HTTP_200_OK,
            serializer_class=serializer_class,
            message = "Registration complete! Log in now to explore and enjoy our platform. Welcome aboard!",
            )
    }
    
    @swagger_auto_schema(operation_id='Signup', responses={**common_post_response})

    def post(self, request):
        """
        Handle POST request for user signup.
        """

        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            # Check if the checkbox is checked
            agreed_to_terms = request.data.get('agreed_to_terms', False)
            if not agreed_to_terms:
                if request.accepted_renderer.format == 'html':
                    return Response(
                        {'serializer': serializer, 'error_message': 'You must agree to the Terms and Conditions.'},
                        template_name=self.template_name,
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                else:
                    return create_api_response(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="You must agree to the Terms and Conditions."
                    )


            user = serializer.save()
            user.set_password(serializer.validated_data["password"])
            user.enforce_password_change = True

            user.save()

            context = {
                'user': user,
                'site_url': get_site_url(request)
            }

            email = Email()  # Replace with your Email class instantiation

            email.send_mail(user.email, 'email_templates/welcome.html', context, 'Welcome to Infinity Fire Prevention Ltd - Your Journey Begins Here')

            # Respond with success message as needed
            if request.accepted_renderer.format == 'html':
                messages.success(request, "Registration complete! Log in now to explore and enjoy our platform. Welcome aboard!")
                return redirect(reverse('login'))
            else:
                return create_api_response(
                    status_code=status.HTTP_201_CREATED,
                    message="Registration complete! Log in now to explore and enjoy our platform. Welcome aboard!"
                    )

            email.send_mail(user.email, 'email_templates/welcome.html', context, 'Welcome to  Infinity Fire Prevention Ltd - Your Journey Begins Here')
            #check admin email
            email_template = EmailNotificationTemplate.objects.filter(purpose = "new_user_registration")
            if email_template:
                email_template = email_template.first()
                context = {'user':user}
                email.send_mail(email_template.recipient, 'email_templates/admin_new_user_registration.html', context, email_template.subject)
            # Redirect or respond with success message as needed
            messages.success(request, "User registered successfully. Please login here.")
            return redirect(reverse('login'))

        else:
            # Render the HTML template with invalid serializer data or return API response with validation errors
            if request.accepted_renderer.format == 'html':
                return render_html_response({'serializer': serializer}, self.template_name)
            else:
                return create_api_response(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="Validation errors",
                    data=serializer.errors
                )

        
class LogoutView(APIView):

    """
    View for user logout.
    """

    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    authentication_classes = [SessionAuthentication, TokenAuthentication]
        
    common_post_response = {
    status.HTTP_200_OK: 
        docs_schema_response_new(
            status_code=status.HTTP_200_OK,
            message = "User logged out successfully",
            )
    }
    
    @swagger_auto_schema(operation_id='Logout', responses={**common_post_response})

    def get(self, request):
        # self.handle_unauthenticated()
        """
        Handle GET request for user logout.
        """

        if request.accepted_renderer.format == 'html':
            if self.request.user.is_authenticated:
                logout(request)
            
                # Redirect to a specific page after logout (you can change 'login' to the desired page name)
                return redirect(reverse('login'))
            else:
                messages.warning(request, "Please login first.")
                # Redirect to a specific page after logout (you can change 'login' to the desired page name)
                return redirect(reverse('login'))
        else:
            
            # Delete the user's token if it exists
            try:
                user_token = Token.objects.get(user=request.user)
                user_token.delete()
            except Token.DoesNotExist:
                # If the client accepts other formats, serialize the data and return an API response
                return create_api_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Please Login First. ",
                )

            # If the client accepts other formats, serialize the data and return an API response
            return create_api_response(
                status_code=status.HTTP_200_OK,
                message="User logged out successfully !",
            )


class ForgotPasswordView(APIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    serializer_class = ForgotPasswordSerializer
    template_name = "forgot.html"
    swagger_schema = None

    def get(self, request):
        """
        Handle GET request for login page.
        """
        if self.request.user.is_authenticated:
            return redirect(reverse('dashboard'))
        
        serializer = self.serializer_class()
        # Render the HTML template for login page
        return render_html_response({'serializer': serializer}, self.template_name)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data.get('email')
        
            try:
                user = User.objects.get(email=email, is_superuser = False)
                # Email exists in the system, proceed with sending the OTP
                token = default_token_generator.make_token(user)
                uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
                user.reset_token = token
                user.token_expiry = timezone.now() + timezone.timedelta(minutes=30)
                user.save()
                reset_url = reverse('password_reset_confirm', args=[uidb64, token])
                site_url = get_site_url(request)
        
                context = {
                    'user': user,
                    'redirect_link': reset_url,
                    'site_url': site_url,
                }
                # email = Email()  # Replace with your Email class instantiation
                # email.send_mail(user.email, 'email_templates/forgot_password.html', context, 'Reset Your Password')
                messages.success(request, f"Please note that an OTP (One-Time Password) has been sent to the email address {user.email}.")
                return redirect(reverse('login'))

            except User.DoesNotExist:
                # Email does not exist in the system
                messages.error(request, f"We apologize, but it seems that the email {email} is not associated with our records.")
                return render_html_response({'serializer': serializer}, self.template_name)
            

        else:
            # Invalid serializer data
            # Render the HTML template with invalid serializer data
            return render_html_response({'serializer': serializer}, self.template_name)


class ResetPasswordView(APIView):
    
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = "reset_password.html"  # Use your actual template name
    serializer_class = ResetPasswordSerializer
    swagger_schema = None

    
    def get(self, request, *args, **kwargs):
        """
        Handle GET request for reset password page.
        """
        if self.request.user.is_authenticated:
            return redirect(reverse('dashboard'))
       
        serializer = self.serializer_class()
        
        # Extract token and uidb64 from the URL kwargs
        token = kwargs['token']
        uidb64 = kwargs['uidb64']
        try:
            uid = urlsafe_base64_decode(uidb64).decode()  # Decoding uidb64 to get user ID
            user = User.objects.get(pk=uid)
           
            # Check if the token is valid for the user
            if default_token_generator.check_token(user, token):
                # Token is valid, render the reset password page
                return render_html_response({'serializer': serializer}, self.template_name)
            else:
                messages.error(request, "Invalid token. Please request a new password reset link.")
                return redirect(reverse('forgot_password'))  # Redirect to the forgot password page
            
        except (User.DoesNotExist, ValueError, OverflowError):
            messages.error(request, "Invalid link. Please request a new password reset link.")
            return redirect(reverse('forgot_password'))  # Redirect to the forgot password page
    
    

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            new_password = serializer.validated_data['password']
            
            # Extract token and uidb64 from the URL kwargs
            token = kwargs['token']
            uidb64 = kwargs['uidb64']
            
            try:
                uid = urlsafe_base64_decode(uidb64).decode()  # Decoding uidb64 to get user ID
                user = User.objects.get(pk=uid)
                
                # Check if the token is valid for the user
                if default_token_generator.check_token(user, token):
                    # Token is valid, update the user's password
                    user.set_password(new_password)
                    user.save()
                    
                    context = {
                    'user': user,
                    'site_url':get_site_url(request)
                    }
                    # email = Email()  # Replace with your Email class instantiation
                    # email.send_mail(user.email, 'email_templates/rest_password.html', context, 'Password Reset Confirmation')
                    
                    messages.success(request, "Your password has been reset successfully. You can now log in with your new password.")
                    return redirect(reverse('login'))  # Redirect to the login page
                
                else:
                    messages.error(request, "Invalid token. Please request a new password reset link.")
                    return redirect(reverse('login'))  # Redirect to the forgot password page
            
            except (User.DoesNotExist, ValueError, OverflowError):
                messages.error(request, "Invalid link. Please request a new password reset link.")
                return redirect(reverse('login'))  # Redirect to the forgot password page
        
        else:
            # Invalid form submission
            # Render the HTML template with invalid serializer data
            return render_html_response({'serializer': serializer}, self.template_name)
    

class ProfileView(APIView):
    
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    serializer_class = UserProfileSerializer
    template_name = "profile.html"
    swagger_schema = None


    def get(self, request):
        """
        Handle GET request for login page.
        """
        # return redirect(reverse('dashboard'))
        

        serializer = self.serializer_class(instance=request.user)
        # Render the HTML template for login page
        return render_html_response({'serializer': serializer}, self.template_name)
    
    def post(self, request):
        data = request.data.copy()  # Create a mutable copy of request.data
        data.update({'email': request.user.email})  # Update the copy with the new email value

        serializer = self.serializer_class(data=data, instance=request.user)
        if serializer.is_valid():
            serializer.save()
            messages.success(request, f"Profile Updated: Your changes have been saved successfully! Thank you for keeping your information up to date")
            return redirect(reverse('profile'))

        else:
            return render_html_response({'serializer': serializer}, self.template_name)


class ChangePasswordView(APIView):
    
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    serializer_class = ChangePasswordSerializer
    template_name = "change_password.html"
    swagger_schema = None


    def get(self, request):
        """
        Handle GET request for login page.
        """
        # return redirect(reverse('dashboard'))
        
        serializer = self.serializer_class()
        # Render the HTML template for login page

        return render_html_response({'serializer': serializer}, self.template_name)

    def post(self, request):
        data = request.data
        serializer = self.serializer_class(data=data, instance=request.user, context={'request': request})

        if serializer.is_valid():
            serializer.save()

            if request.accepted_renderer.format == 'json':
                return create_api_response(
                    status_code=status.HTTP_200_OK,
                    message="Password updated successfully."
                )
            else:
                messages.success(request, "Password updated successfully. Please use your new password for future logins.")
                return redirect(reverse('profile'))
        else:
            if request.accepted_renderer.format == 'json':
                return create_api_response(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="Validation errors",
                    data=serializer.errors
                )
            else:
                return render_html_response({'serializer': serializer}, self.template_name)




class EnforceChangePasswordView(APIView):
    
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    serializer_class = ChangePasswordSerializer
    template_name = "enforce_password_change.html"

    
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
            user = serializer.save()
            user.enforce_password_change = True
            user.save()
            messages.success(request, f"Password updated successfully. Please use your new password for future logins.")
            return redirect(reverse('dashboard'))

        else:
            return self.render_html_response(serializer)

