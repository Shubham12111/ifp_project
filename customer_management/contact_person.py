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
    queryset = ContactPerson.objects.all()

    def get_customer(self):
        customer_id = self.kwargs.get('customer_id', '')
        if customer_id:
            return User.objects.filter(id=customer_id).first()
        return None
    
    def get_queryset(self, customer):
        """
        Get the queryset for listing Conatct items.

        Returns:
            QuerySet: A queryset of Conatct items filtered based on the authenticated user's ID.
        """
        queryset = super().get_queryset()
        if customer and queryset:
            queryset = queryset.filter(customer=customer.customermeta).all()
            return queryset
        return None
    
    def get_object(self, queryset):
        pk=self.kwargs.get('address_id', None)
        instance = None
        if pk and queryset:
            instance = queryset.filter(pk=pk).first()
            return instance
        return instance
    
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
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        customer = self.get_customer()
        if not customer:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('customer_list'))

        queryset = self.get_queryset(customer)
        instance = self.get_object(queryset)
        if not instance and kwargs.get('address_id', ''):
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('customer_contact_person', kwargs={'customer_id': customer.id}))

        serializer = self.serializer_class(instance=instance) if instance else self.serializer_class()

        if request.accepted_renderer.format == 'html':
            context = {
                'serializer':serializer, 
                'customer_instance': customer,
                'contact_person_list': queryset
            }
            return render_html_response(context,self.template_name)
        else:
            messages.error(request, "Customer not found OR You are not authorized to perform this action.")
            return redirect(reverse('customer_list'))
            
    def post(self, request, *args, **kwargs):
        customer = self.get_customer()
        if not customer:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('customer_list'))

        queryset = self.get_queryset(customer)
        instance = self.get_object(queryset)
        if not instance and kwargs.get('address_id', ''):
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('customer_contact_person', kwargs={'customer_id': customer.id}))

        serializer = self.serializer_class(data=request.data, instance=instance) if instance else self.serializer_class(data=request.data)
        message = f"Your Customer contact person has been {'updated' if instance else 'added'} successfully!"

        if serializer.is_valid():
            serializer.validated_data['customer'] = customer.customermeta
            # If the serializer data is valid, save the billing address instance.
            serializer.update(instance=instance, validated_data=serializer.validated_data) if instance else serializer.save()


            if request.accepted_renderer.format == 'html':
                # For HTML requests, display a success message and redirect to the customer's billing address list.
                messages.success(request, message)
                return redirect(reverse('customer_contact_person', kwargs={'customer_id': kwargs['customer_id']}))
            else:
                # For API requests, return a success response with serialized data.
                return create_api_response(message=message, data=serializer.data, status=status.HTTP_200_OK)
        else:
            message = "Unable to submit your data please validate and try again."
            if request.accepted_renderer.format == 'html':
                # For HTML requests with invalid data, render the template with error messages.
                context = {
                    'serializer':serializer, 
                    'customer_instance': customer,
                    'site_address_list': queryset
                }
                return render(request, self.template_name, context)
            else:
                # For API requests with invalid data, return an error response with serializer errors.
                return create_api_response(message=message, data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerRemoveContactPersonView(CustomAuthenticationMixin, generics.DestroyAPIView):
    """
    View to remove a ContactPerson associated with a Customer.
    """
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    swagger_schema = None
    queryset = ContactPerson.objects.all()

    def get_customer(self):
        customer_id = self.kwargs.get('customer_id', '')
        if customer_id:
            return User.objects.filter(id=customer_id).first()
        return None
    
    def get_queryset(self, customer):
        """
        Get the queryset for listing Conatct items.

        Returns:
            QuerySet: A queryset of Conatct items filtered based on the authenticated user's ID.
        """
        queryset = super().get_queryset()
        if customer and queryset:
            queryset = queryset.filter(customer=customer.customermeta).all()
            return queryset
        return None
    
    def get_object(self, queryset):
        pk=self.kwargs.get('address_id', None)
        instance = None
        if pk and queryset:
            instance = queryset.filter(pk=pk).first()
            return instance
        return instance
    
    def destroy(self, request, *args, **kwargs):
        """
        Handles DELETE request to remove the document associated with a conversation.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"customer", HasUpdateDataPermission, 'change'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        customer = self.get_customer()
        if not customer:
            messages.error(request, "You are not authorized to perform this action")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND, message='You are not authorized to perform this action')

        queryset = self.get_queryset(customer)
        instance = self.get_object(queryset)
        if not instance and kwargs.get('address_id', ''):
            messages.error(request, "You are not authorized to perform this action")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND, message='You are not authorized to perform this action')
        
        if instance.user:
            instance.user.delete()
        
        instance.delete()

        messages.success(request, 'Customer contact person has been deleted successfully!')
        return create_api_response(status_code=status.HTTP_200_OK, message='Customer contact person has been deleted successfully!' )


class CustomerContactPersonDetailView(CustomAuthenticationMixin, generics.CreateAPIView):
    """
    View for adding or updating a contact.
    Supports both HTML and JSON response formats.
    """
    serializer_class = ContactPersonSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'customer_contact_view.html'
    swagger_schema = None
    queryset = ContactPerson.objects.all()

    def get_customer(self):
        customer_id = self.kwargs.get('customer_id', '')
        if customer_id:
            return User.objects.filter(id=customer_id).first()
        return None
    
    def get_queryset(self, customer):
        """
        Get the queryset for listing Conatct items.

        Returns:
            QuerySet: A queryset of Conatct items filtered based on the authenticated user's ID.
        """
        queryset = super().get_queryset()
        if customer and queryset:
            queryset = queryset.filter(customer=customer.customermeta).all()
            return queryset
        return None
    
    def get_object(self, queryset):
        pk=self.kwargs.get('address_id', None)
        instance = None
        if pk and queryset:
            instance = queryset.filter(pk=pk).first()
            return instance
        return instance
        
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
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect
        
        customer = self.get_customer()
        if not customer:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('customer_list'))

        queryset = self.get_queryset(customer)
        instance = self.get_object(queryset)
        if not instance:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('customer_contact_person', kwargs={'customer_id': customer.id}))

        serializer = self.serializer_class(instance=instance)

        if request.accepted_renderer.format == 'html':
            context = {
                'serializer':serializer.data, 
                'customer_instance': customer,
                'customer_id': customer.id,
                'contact_person_list': queryset
            }
            return render_html_response(context,self.template_name)
        else:
            messages.error(request, "Customer not found OR You are not authorized to perform this action.")
            return redirect(reverse('customer_list'))
