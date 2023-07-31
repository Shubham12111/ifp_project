from rest_framework.views import exception_handler
from rest_framework.response import Response
from django.http import JsonResponse
from django.shortcuts import render

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None and response.status_code == 403:
        # Access the request object from the context
        request = context['request']
        # Customize the response based on the requested format
        if request.accepted_renderer.format == 'html':
            return render_custom_html_page()
        else:
            response_data = {
                'detail': 'You do not have permission to perform this action.'
            }
            return JsonResponse(response_data, status=403)

    return response

def render_custom_html_page():
    # Implement your custom HTML page rendering logic here
    # For example, you can use Django's render function
    # to render a template with a custom message for 403 Forbidden
    return render(None, 'custom_403.html', status=403)
