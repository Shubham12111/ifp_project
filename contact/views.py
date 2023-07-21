
from django.contrib import messages
from django.views import View
from django.urls import reverse
from django.shortcuts import render,redirect
from django.http import Http404
from django.http import JsonResponse

from rest_framework import generics, status, filters
from django.shortcuts import render
from django.views import View
from .models import *
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.renderers import TemplateHTMLRenderer,JSONRenderer
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


from infinity_fire_solutions.response_schemas import create_api_response,convert_serializer_errors
from cities_light.models import City, Country, Region

from .models import Contact
from .serializers import ContactSerializer


class ContactListView(generics.ListAPIView):
    """ view to get the listing of all contacts
    """
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'email','contact_type__name']
    template_name = 'contact_list.html'
    ordering_fields = ['created_at'] 

    def get(self, request, *args, **kwargs):
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            return self.handle_ajax_request(request)
        else:
            return self.handle_html_request(request)
    
    def handle_ajax_request(self, request):
        queryset = self.get_queryset()

        # Apply filtering based on DataTables' search query
        search_query = request.GET.get('search[value]')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(contact_type__name__icontains=search_query)
            )

        # Count the total number of records before applying pagination
        total_records = queryset.count()

        # Apply ordering based on DataTables' request
        order_column_idx = int(request.GET.get('order[0][column]'))
        order_column_name = self.ordering_fields[order_column_idx]
        order_direction = request.GET.get('order[0][dir]')
        if order_direction == 'desc':
            order_column_name = f"-{order_column_name}"
        queryset = queryset.order_by(order_column_name)

        # Apply pagination based on DataTables' request
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        queryset = queryset[start:start + length]

        # Serialize the data and return the JSON response
        serializer = self.serializer_class(queryset, many=True)

        return JsonResponse({
            'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': total_records,
            'recordsFiltered': queryset.count(),
            'data': serializer.data,
        })

    def handle_html_request(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if request.accepted_renderer.format == 'html':
            # If the client accepts HTML, render the template
            return Response({'contacts': queryset}, template_name=self.template_name)
        
       # If the client accepts JSON, serialize the data and return it
        serializer = self.serializer_class(queryset, many=True)

        return create_api_response(status_code=status.HTTP_200_OK,
                                    message="Data retrieved",
                                    data=serializer.data)

    

class ContactAddUpdateView(APIView):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    # permission_classes = [IsAuthenticated]
    template_name = 'contact.html'

    def render_html_response(self, serializer):
        """
        Render HTML response using the provided serializer and template name.
        """
        return Response({'serializer': serializer}, template_name=self.template_name)
    

    def get(self, request, *args, **kwargs):
        if kwargs.get('pk'):  # If a primary key is provided, it means we are editing an existing contact
            contact = self.get_object(kwargs['pk'])
            serializer = self.serializer_class(instance=contact)
            return self.render_html_response(serializer)
        else:
            serializer = self.serializer_class()
            return self.render_html_response(serializer)
        
    def get_object(self, pk):
        try:
            return Contact.objects.get(pk=pk)
        except Contact.DoesNotExist:
            raise Http404



    def post(self, request, *args, **kwargs):
        if kwargs.get('pk'):
            # If a primary key is provided, it means we are editing an existing contact
            contact = self.get_object(kwargs['pk'])
            serializer = self.serializer_class(contact, data=request.data)
        else:
            # If no primary key is provided, it means we are adding a new contact
            serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            if request.user.is_authenticated:  # Check if the user is authenticated
                serializer.validated_data['user_id'] = request.user  # Assign the current user instance
            serializer.save()

            if request.accepted_renderer.format == 'html':
                # Render the HTML template with invalid serializer data
                if kwargs.get('pk'):
                    messages.success(request, "Great! your contact has been updated successfully.")
                else:
                    messages.success(request, "Congratulations! your contact has been added successfully.")
                return redirect(reverse('contact_list'))

            else:
            # Return JSON response with success message and serialized data
                return create_api_response(status_code=status.HTTP_201_CREATED,
                                       message="Congratulations! your contact has been added/updated successfully.",
                                       data=serializer.data
                                       )
        else:
        # Invalid serializer data
            if request.accepted_renderer.format == 'html':
                # Render the HTML template with invalid serializer data
                return self.render_html_response(serializer)
            else:   
                # Return JSON response with error message
                return create_api_response(status_code=status.HTTP_400_BAD_REQUEST,
                                       message="We apologize for the inconvenience, but please review the below information.",
                                       data=convert_serializer_errors(serializer.errors))

            
class ContactDeleteView(APIView):
    serializer_class = ContactSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    # permission_classes = [IsAuthenticated]
    template_name = 'contact.html'

    def get(self, request, *args, **kwargs):
        if kwargs.get('pk'):  # If a primary key is provided, it means we are editing an existing contact
            contact = self.get_object(kwargs['pk'])
            serializer = self.serializer_class(instance=contact)
        else:
            serializer = self.serializer_class()
        if request.accepted_renderer.format == 'html':
            # If the client accepts HTML, render the template
            return Response({'serializer': serializer}, template_name=self.template_name)
        
    def get_object(self, pk):
        try:
            return Contact.objects.get(pk=pk)
        except Contact.DoesNotExist:
            raise Http404
               
    def delete(self, request, *args, **kwargs):
        # Get the contact instance from the database
        contact = self.get_object(kwargs['pk'])

        # Proceed with the deletion
        contact.delete()
        
        if request.accepted_renderer.format == 'html':
            messages.success(request, "Your contact has been deleted successfully!")
            return redirect(reverse('contact_list'))
        else:
            return create_api_response(status_code=status.HTTP_200_OK,
                                       message="Your contact has been deleted successfully!")  

      
      
class MessageListView(View):
    template_name = 'messages.html'

    def get(self, request):
        messages = Contact.objects.all()
        return render(request, self.template_name, {'messages': messages})

