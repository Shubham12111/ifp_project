from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import render

def custom_exception_handler(exc, context):
    if isinstance(exc, PermissionDenied):
        # Customize the response data as per your requirements
        custom_response_data = {
            'detail': 'You do not have permission to perform this action.',
        }

        # Return a DRF Response with the custom data and status code 403
        return Response(custom_response_data, status=status.HTTP_403_FORBIDDEN)

    # For other exceptions, use the default exception handler or customize as needed
    return exception_handler(exc, context)
