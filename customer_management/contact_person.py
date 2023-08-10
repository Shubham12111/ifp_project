from django.shortcuts import render, redirect
from django.http import Http404, JsonResponse, HttpResponse
from django.conf import settings
from infinity_fire_solutions.aws_helper import *
from infinity_fire_solutions.permission import *
from .models import *
from .serializers import ContactPersonSerializer
from infinity_fire_solutions.response_schemas import create_api_response, render_html_response
from django.contrib import messages
from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer

class CustomerContactPersonView(CustomAuthenticationMixin, generics.CreateAPIView):
    """
    View for adding or updating a contact.
    Supports both HTML and JSON response formats.
    """
    serializer_class = ContactPersonSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'customer_contact_person.html'
    swagger_schema = None
    def get_contact_person(self):
        contact_person_list = ContactPerson.objects.filter(user_id__id=self.kwargs.get('customer_id'))
    
        return contact_person_list
    
    def get_queryset(self):
        """
        Get the queryset for listing Conatct items.

        Returns:
            QuerySet: A queryset of Conatct items filtered based on the authenticated user's ID.
        """
        # Get the model class using the provided module_name string
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "customer", HasUpdateDataPermission, 'change'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(created_by=self.request.user ),
            "all": Q(),  # An empty Q() object returns all data
        }

        # Get the appropriate filter from the mapping based on the data access value,
        # or use an empty Q() object if the value is not in the mapping
        queryset = User.objects.filter(filter_mapping.get(data_access_value, Q()), roles__name__icontains='customer')
        queryset = queryset.filter(pk=self.kwargs.get('customer_id')).first()
        return queryset

    def get_contact_person_instance(self):
        
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "customer", HasUpdateDataPermission, 'change'
        )
        
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(user_id__created_by=self.request.user ),
            "all": Q(),  # An empty Q() object returns all data
        }
        
        contact_person = ContactPerson.objects.filter(filter_mapping.get(data_access_value, Q()))
        contact_person = contact_person.filter(user_id__id=self.kwargs.get('customer_id'),
                                                       pk=self.kwargs.get('address_id')).first()
        return contact_person
        
    def get(self, request, *args, **kwargs):
        """
        Handle GET request to display a form for updating a contact.
        If the contact exists, retrieve the serialized data and render the HTML template.
        If the contact does not exist, render the HTML template with an empty serializer.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"customer", HasUpdateDataPermission, 'change'
        )
        if request.accepted_renderer.format == 'html':
            address_instance = self.get_contact_person_instance()
            if address_instance:
                serializer = self.serializer_class(instance=address_instance)
            else:
                serializer = self.serializer_class()
            
            queryset = self.get_queryset()
            if queryset:
                context = {'serializer':serializer, 
                        'customer_instance':queryset,
                        'contact_person_list':self.get_contact_person()}
                return render_html_response(context,self.template_name)
            
            else:
                messages.error(request, "Customer not found.")
                return redirect(reverse('customer_list'))
        else:
            return create_api_response(status_code=status.HTTP_201_CREATED,
                                message="GET Method Not Alloweded",)
            
    def post(self, request, *args, **kwargs):
        data = request.data
        company_instance = self.get_queryset()

        # Check if the company instance exists
        if company_instance:
            address_instance = self.get_contact_person_instance()

            # Check if the contact person instance exists for the customer
            if address_instance:
                # If the contact person instance exists, update it.
                serializer = self.serializer_class(data=data, instance=address_instance, context={'request': request})
                message = "Your Customer contact person has been updated successfully!"
            else:
                # If the contact person instance does not exist, create a new one.
                serializer = self.serializer_class(data=data, context={'request': request})
                message = "Your Customer contact person has been added successfully!"

            if serializer.is_valid():
                # If the serializer data is valid, save the contact person instance.
                if not address_instance:
                    serializer.validated_data['user_id'] = company_instance
                serializer.save()

                if request.accepted_renderer.format == 'html':
                    # For HTML requests, display a success message and redirect to the customer's contact person list.
                    messages.success(request, message)
                    return redirect(reverse('customer_contact_person', kwargs={'customer_id': kwargs['customer_id']}))
                else:
                    # For API requests, return a success response with serialized data.
                    return Response({'message': message, 'data': serializer.data}, status=status.HTTP_200_OK)
            else:
                if request.accepted_renderer.format == 'html':
                    # For HTML requests with invalid data, render the template with error messages.
                    context = {'serializer': serializer,
                                'customer_instance': self.get_queryset(),
                                'contact_person_list': self.get_contact_person()}
                    return render(request, self.template_name, context)
                else:
                    # For API requests with invalid data, return an error response with serializer errors.
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            # If the company instance does not exist, return an error response.
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('customer_list'))



class CustomerRemoveContactPersonView(CustomAuthenticationMixin, generics.DestroyAPIView):
    """
    View to remove a ContactPerson associated with a Customer.
    """
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    swagger_schema = None
    def get_queryset(self):
        """
        Get the queryset of contacts filtered by the current user.
        """
         # Get the model class using the provided module_name string
    
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "customer", HasDeleteDataPermission, 'delete'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(user_id__created_by=self.request.user ),
            "all": Q(),  # An empty Q() object returns all data
        }
        
        contact_person = ContactPerson.objects.filter(filter_mapping.get(data_access_value, Q()))
        
        contact_person = contact_person.filter(user_id__id=self.kwargs.get('customer_id'),
                                                       pk=self.kwargs.get('address_id')).first()
        
        return contact_person
    
    def destroy(self, request, *args, **kwargs):
        """
        Handles DELETE request to remove the document associated with a conversation.
        """
        contact_person = self.get_queryset()
        if contact_person:
            # Proceed with the deletion
            contact_person.delete()
            success_message = "Customer contact person has been deleted successfully!"
            messages.success(request,success_message)
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,message=success_message )
        else:
            error_message= "Customer contact person not found"
            messages.error(request,error_message)
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message=error_message, )


        
