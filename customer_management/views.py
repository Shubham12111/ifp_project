from django.shortcuts import render, redirect
from django.http import Http404, JsonResponse, HttpResponse
from django.conf import settings
from infinity_fire_solutions.aws_helper import *
from infinity_fire_solutions.permission import *
from .models import *
from .serializers import CustomerSerializer #, ConversationSerializer, ConversationViewSerializer
from infinity_fire_solutions.response_schemas import create_api_response, convert_serializer_errors, render_html_response
from django.contrib import messages
from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from django.http import HttpResponseRedirect


class CustomerListView(CustomAuthenticationMixin,generics.ListAPIView):
    """
    View to get the listing of all contacts.
    Supports both HTML and JSON response formats.
    """
    serializer_class = CustomerSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'email']
    template_name = 'customer_list.html'
    ordering_fields = ['created_at'] 

    def get(self, request, *args, **kwargs):
        """
        Handle both AJAX (JSON) and HTML requests.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self,"customer", HasListDataPermission, 'list'
        )
        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(user_id=request.user),
            "all": Q(),  # An empty Q() object returns all data
        }
        user_role = UserRole.objects.filter(name='Customer').first()
        # Get the appropriate filter from the mapping based on the data access value,
        # or use an empty Q() object if the value is not in the mapping
        queryset = User.objects.filter(filter_mapping.get(data_access_value, Q()), roles=user_role).exclude(pk=request.user.id)
        print(queryset)
        if request.accepted_renderer.format == 'html':
            context = {'customers':queryset}
            return render_html_response(context,self.template_name)
        else:
            serializer = self.serializer_class(queryset, many=True)
            return create_api_response(status_code=status.HTTP_200_OK,
                                            message="Data retrieved",
                                            data=serializer.data)


class CustomerView(CustomAuthenticationMixin, generics.CreateAPIView):
    """
    View for adding or updating a customer.
    Supports both HTML and JSON response formats.
    """
    serializer_class = CustomerSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'customer.html'

    
    def get_queryset(self):
        """
        Get the filtered queryset for customers based on the authenticated user.
        """
        queryset = User.objects.filter(pk=self.kwargs.get('pk'),user_id=self.request.user.id).order_by('-created_at').first()
        return queryset

    def get(self, request, *args, **kwargs):
        """
        Handle GET request to display a form for updating a customer.
        If the customer exists, retrieve the serialized data and render the HTML template.
        If the customer does not exist, render the HTML template with an empty serializer.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"customer", HasCreateDataPermission, 'add'
        )
           
        if request.accepted_renderer.format == 'html':
            context = {'serializer':self.serializer_class()}
            return render_html_response(context,self.template_name)
        else:
            return create_api_response(status_code=status.HTTP_201_CREATED,
                                message="GET Method Not Alloweded",)
        
