from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from django.contrib import messages

from .serializers import LoginSerializer
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

    def get(self, request, *args, **kwargs):
        """
        Handle GET request for login page.
        """
        serializer = self.serializer_class()

        if request.accepted_renderer.format == 'html':
            # Render the HTML template for login page
            return self.render_html_response(serializer)
        else:
            # Return JSON response with error message
            return create_api_response(status_code=status.HTTP_400_BAD_REQUEST,
                                       message="Please ensure that the entered details are correct and try again.",
                                       data=serializer.data)

    def post(self, request, *args, **kwargs):
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
                # coming from the webiste TODO
                if request.accepted_renderer.format == 'html' and 'HTTP_USER_AGENT' in request.META:
                    # Render the HTML template with error message
                    messages.error(request, 'Login failed. The credentials provided are incorrect. Please verify your login information and try again.')
                    return self.render_html_response(serializer)
                else:
                    # Return JSON response with error message
                    return create_api_response(status_code=status.HTTP_400_BAD_REQUEST,
                                                message="Please ensure that the entered details are correct and try again.",
                                                data=serializer.errors)

            # User authentication successful
            user = user
            token = Token.objects.get_or_create(user=user)

            if request.accepted_renderer.format == 'html' and 'HTTP_USER_AGENT' in request.META:
                # Render the HTML template for successful login
                return self.render_html_response(serializer)
            else:
                # Return JSON response with token
                return create_api_response(status_code=status.HTTP_200_OK,
                                            message="Please ensure that the entered details are correct and try again.",
                                            data={'token':token[0].key})

        else:
            # Invalid serializer data
            if request.accepted_renderer.format == 'html':
                # Render the HTML template with invalid serializer data
                return self.render_html_response(serializer)
            else:
                # Return JSON response with error message
                return create_api_response(status_code=status.HTTP_400_BAD_REQUEST,
                                            message="Please ensure that the entered details are correct and try again.",
                                            data=serializer.errors)
