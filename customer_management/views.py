from django.shortcuts import render, redirect
from django.http import Http404, JsonResponse, HttpResponse
from django.conf import settings
from infinity_fire_solutions.aws_helper import *
from infinity_fire_solutions.permission import *
from .models import *
from .serializers import CustomerSerializer , BillingAddressSerializer#, ConversationSerializer, ConversationViewSerializer
from infinity_fire_solutions.response_schemas import create_api_response, convert_serializer_errors, render_html_response
from django.contrib import messages
from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
import random
import string
from infinity_fire_solutions.custom_form_validation import *
from infinity_fire_solutions.email import *
from contact.models import Contact


def generate_strong_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for _ in range(length))
    return password



class CustomerListView(CustomAuthenticationMixin,generics.ListAPIView):
    """
    View to get the listing of all contacts.
    Supports both HTML and JSON response formats.
    """
    serializer_class = CustomerSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    filter_backends = [filters.SearchFilter]
    search_fields = ['first_name','last_name', 'email','company_name']
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
            "self": Q(created_by=request.user),
            "all": Q(),  # An empty Q() object returns all data
        }
        # Get the appropriate filter from the mapping based on the data access value,
        # or use an empty Q() object if the value is not in the mapping
        queryset = User.objects.filter(filter_mapping.get(data_access_value, Q()), roles__name='Customer').exclude(pk=request.user.id)
        if request.accepted_renderer.format == 'html':
            context = {'customers':queryset}
            return render_html_response(context,self.template_name)
        else:
            serializer = self.serializer_class(queryset, many=True)
            return create_api_response(status_code=status.HTTP_200_OK,
                                            message="Data retrieved",
                                            data=serializer.data)

class CustomerAddView(CustomAuthenticationMixin, generics.CreateAPIView):
    """
    View for adding or updating a customer.
    Supports both HTML and JSON response formats.
    """
    serializer_class = CustomerSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'customer.html'

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
        
        contact_id = kwargs.get('contact_id')
        if contact_id:
            contact = Contact.objects.get(pk=contact_id)
            serializer = self.serializer_class(contact)  # Serialize the contact data
            print(serializer)
        else:
            serializer = self.serializer_class()  # Create an empty serializer
        if request.accepted_renderer.format == 'html':
            context = {'serializer':serializer}
            return render_html_response(context,self.template_name)
        else:
            return create_api_response(status_code=status.HTTP_201_CREATED,
                                message="GET Method Not Alloweded",)
        
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to add or update a customer.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"customer", HasCreateDataPermission, 'add'
        )
        message = "Congratulations! your customer has been added successfully."
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.save()
            #check the User Role 
            user_role = UserRole.objects.filter(name="Customer").first()
            if user_role:
                user_role = user_role
            else:
                user_role = UserRole.objects.create(name="Customer")
            
            user.roles = user_role
            user.created_by = request.user 
            user.save()
            
            # Generate a strong password
            strong_password = generate_strong_password()
            user.set_password(strong_password)
            user.save()
                    
            site_url = get_site_url(request)
        
            context = {
                'user': user,
                'site_url': site_url,
                'user_password':strong_password
            }
            email = Email()  # Replace with your Email class instantiation
            email.send_mail(user.email, 'email_templates/customer_password.html', context, 'Your New Account Password')
            
            if request.accepted_renderer.format == 'html':
                messages.success(request, message)
                return redirect(reverse('customer_list'))

            else:
                # Return JSON response with success message and serialized data
                return create_api_response(status_code=status.HTTP_201_CREATED,
                                    message=message,
                                    data=serializer.data
                                    )
        else:
            # Invalid serializer data
            if request.accepted_renderer.format == 'html':
                # Render the HTML template with invalid serializer data
                context = {'serializer':serializer}
                return render_html_response(context,self.template_name)
            else:   
                # Return JSON response with error message
                return create_api_response(status_code=status.HTTP_400_BAD_REQUEST,
                                    message="We apologize for the inconvenience, but please review the below information.",
                                    data=convert_serializer_errors(serializer.errors))

class CustomerUpdateView(CustomAuthenticationMixin, generics.UpdateAPIView):
    """
    API view for updating a customer.

    This view handles both HTML and API requests for updating a customer instance.
    If the customer instance exists, it will be updated with the provided data.
    Otherwise, an error message will be returned.

    The following request methods are supported:
    - POST: Updates the customer instance.

    Note: Make sure to replace 'your_template_name.html' with the appropriate HTML template name.
    """
    
    serializer_class = CustomerSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'customer.html'


    
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
        
        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(created_by=self.request.user ),
            "all": Q(),  # An empty Q() object returns all data
        }

        # Get the appropriate filter from the mapping based on the data access value,
        # or use an empty Q() object if the value is not in the mapping
        queryset = User.objects.filter(filter_mapping.get(data_access_value, Q()), roles__name='customer')
        queryset = queryset.filter(pk=self.kwargs.get('customer_id')).first()
        return queryset

    
    def get(self, request, *args, **kwargs):
        # This method handles GET requests for updating an existing Conatct object.
        if request.accepted_renderer.format == 'html':
            instance = self.get_queryset()
            if instance:
                serializer = self.serializer_class(instance=instance, context={'request': request})
                context = {'serializer': serializer, 'customer_instance': instance}
                return render_html_response(context, self.template_name)
            else:
                messages.error(request, "You are not authorized to perform this action")
                return redirect(reverse('customer_list'))
    
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to update a customer instance.

        Args:
            request (rest_framework.request.Request): The HTTP request object.
            *args: Variable-length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            rest_framework.response.Response: HTTP response object.
                If successful, the customer is updated, and the appropriate response is returned.
                If unsuccessful, an error response is returned.
        """
        data = request.data
        instance = self.get_queryset()
        if instance:
            # If the customer instance exists, initialize the serializer with instance and provided data.
            serializer = self.serializer_class(instance=instance, data=data, context={'request': request})

            if serializer.is_valid():
                # If the serializer data is valid, save the updated customer instance.
                serializer.save()
                message = "Your Customer has been updated successfully!"

                if request.accepted_renderer.format == 'html':
                    # For HTML requests, display a success message and redirect to contact_list.
                    messages.success(request, message)
                    return redirect('customer_list')
                else:
                    # For API requests, return a success response with serialized data.
                    return Response({'message': message, 'data': serializer.data}, status=status.HTTP_200_OK)
            else:
                if request.accepted_renderer.format == 'html':
                    # For HTML requests with invalid data, render the template with error messages.
                    context = {'serializer': serializer, 'instance': instance}
                    return render(request, self.template_name, context)
                else:
                    # For API requests with invalid data, return an error response with serializer errors.
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            error_message = "You are not authorized to perform this action"
            if request.accepted_renderer.format == 'html':
                # For HTML requests with no instance, display an error message and redirect to contact_list.
                messages.error(request, error_message)
                return redirect('customer_list')
            else:
                # For API requests with no instance, return an error response with an error message.
                return Response({'message': error_message}, status=status.HTTP_400_BAD_REQUEST)

class CustomerBillingAddressView(CustomAuthenticationMixin, generics.CreateAPIView):
    """
    View for adding or updating a customer.
    Supports both HTML and JSON response formats.
    """
    serializer_class = BillingAddressSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'customer_billing_address.html'

    def get_billing_address(self):
        billing_address_list = BillingAddress.objects.filter(user_id__id=self.kwargs.get('customer_id'))
    
        return billing_address_list
    
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
        
        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(created_by=self.request.user ),
            "all": Q(),  # An empty Q() object returns all data
        }

        # Get the appropriate filter from the mapping based on the data access value,
        # or use an empty Q() object if the value is not in the mapping
        queryset = User.objects.filter(filter_mapping.get(data_access_value, Q()), roles__name='customer')
        queryset = queryset.filter(pk=self.kwargs.get('customer_id')).first()
        return queryset

    def get_billing_address_instance(self):
        billing_address = BillingAddress.objects.filter(user_id__id=self.kwargs.get('customer_id'),
                                                       pk=self.kwargs.get('address_id')).first()
        return billing_address
        
    def get(self, request, *args, **kwargs):
        """
        Handle GET request to display a form for updating a customer.
        If the customer exists, retrieve the serialized data and render the HTML template.
        If the customer does not exist, render the HTML template with an empty serializer.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"customer", HasCreateDataPermission, 'change'
        )
        if request.accepted_renderer.format == 'html':
            address_instance = self.get_billing_address_instance()
            if address_instance:
                serializer = self.serializer_class(instance=address_instance)
            else:
                serializer = self.serializer_class()
            
            queryset = self.get_queryset()
            if queryset:
                context = {'serializer':serializer, 
                       'customer_instance':self.get_queryset(),
                       'billing_address_list':self.get_billing_address()}
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
            address_instance = self.get_billing_address_instance()

            # Check if the billing address instance exists for the customer
            if address_instance:
                # If the billing address instance exists, update it.
                serializer = self.serializer_class(data=data, instance=address_instance, context={'request': request})
                message = "Your Customer billing address has been updated successfully!"
            else:
                # If the billing address instance does not exist, create a new one.
                serializer = self.serializer_class(data=data, context={'request': request})
                message = "Your Customer billing address has been added successfully!"

            if serializer.is_valid():
                # If the serializer data is valid, save the billing address instance.
                if not address_instance:
                    serializer.validated_data['user_id'] = company_instance
                serializer.save()

                if request.accepted_renderer.format == 'html':
                    # For HTML requests, display a success message and redirect to the customer's billing address list.
                    messages.success(request, message)
                    return redirect(reverse('customer_billing_address', kwargs={'customer_id': kwargs['customer_id']}))
                else:
                    # For API requests, return a success response with serialized data.
                    return Response({'message': message, 'data': serializer.data}, status=status.HTTP_200_OK)
            else:
                if request.accepted_renderer.format == 'html':
                    # For HTML requests with invalid data, render the template with error messages.
                    context = {'serializer': serializer,
                                'customer_instance': self.get_queryset(),
                                'billing_address_list': self.get_billing_address()}
                    return render(request, self.template_name, context)
                else:
                    # For API requests with invalid data, return an error response with serializer errors.
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            # If the company instance does not exist, return an error response.
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('customer_list'))

class CustomerRemoveBillingAddressView(CustomAuthenticationMixin, generics.DestroyAPIView):
    """
    View to remove a BillingAddress associated with a Customer.
    """
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    
    def get_queryset(self):
        """
        Get the queryset of contacts filtered by the current user.
        """
         # Get the model class using the provided module_name string
    
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "customer", HasDeleteDataPermission, 'delete'
        )

        billing_address = BillingAddress.objects.filter(user_id__id=self.kwargs.get('customer_id'),
                                                       pk=self.kwargs.get('address_id')).first()
        print(billing_address)
        return billing_address
    
    def destroy(self, request, *args, **kwargs):
        """
        Handles DELETE request to remove the document associated with a conversation.
        """
        billing_address = self.get_queryset()
        if billing_address:
            # Proceed with the deletion
            billing_address.delete()
            success_message = "Customer biling address has been deleted successfully!"
            messages.success(request,success_message)
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,message=success_message )
        else:
            error_message= "Customer biling address not found"
            messages.error(request,error_message)
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message=error_message, )
    
class CustomerDeleteView(CustomAuthenticationMixin, generics.DestroyAPIView):
    """
    View for deleteing .
    Supports both HTML and JSON response formats.
    """
    serializer_class = CustomerSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    # permission_classes = [IsAuthenticated]
    template_name = 'customer.html'
    
    def delete(self, request, *args, **kwargs):
        """
        Handle DELETE request to delete a customer.
        """
        # Get the customer instance from the database
        # Call the handle_unauthenticated method to handle unauthenticated access

        authenticated_user, data_access_value = check_authentication_and_permissions(
            self,"customer", HasDeleteDataPermission, 'delete'
        )

        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(user_id=request.user ),
            "all": Q(),  # An empty Q() object returns all data
        }

        # Get the appropriate filter from the mapping based on the data access value,
        # or use an empty Q() object if the value is not in the mapping

        queryset = User.objects.filter(filter_mapping.get(data_access_value, Q()), pk=self.kwargs.get('pk'), roles__name='Customer').exclude(pk=request.user.id)
        
        customer = queryset.first()
        
        if customer:
            # Proceed with the deletion
            customer.delete()
            messages.success(request, "Customer has been deleted successfully!")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="Your Customer has been deleted successfully!", )
        else:
            messages.error(request, "Customer not found")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="Customer not found", )
       
