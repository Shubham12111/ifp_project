from django.shortcuts import render, redirect
from django.http import Http404, JsonResponse, HttpResponse
from django.conf import settings
from infinity_fire_solutions.aws_helper import *
from infinity_fire_solutions.permission import *
from .models import *
from .serializers import *
from infinity_fire_solutions.response_schemas import create_api_response, convert_serializer_errors, render_html_response
from django.contrib import messages
from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
import random
import string
from django.core.serializers import serialize
from infinity_fire_solutions.custom_form_validation import *
from infinity_fire_solutions.email import *
from contact.models import Contact
from drf_yasg.utils import swagger_auto_schema
from infinity_fire_solutions.utils import docs_schema_response_new
from customer_management.constants import POST_CODES_INFO

from django.contrib.auth.hashers import make_password

def generate_strong_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for _ in range(length))
    return password


def create_customer(customer, request):
    """
    Create a new customer, assign role, generate password, send email, and save changes.

    Args:
        customer (Customer): The customer instance to be created.
        request (HttpRequest): The request object containing user information.

    Returns:
        None
    """
    # Check if the 'Customer' role exists, otherwise create it
    user_role, created = UserRole.objects.get_or_create(name="Customer")

    # Assign the 'Customer' role and creator to the customer
    customer.roles = user_role
    customer.created_by = request.user
    customer.save()

    # Generate a strong password for the customer
    strong_password = generate_strong_password()  # Implement your generate_strong_password function
    customer.password = make_password(strong_password)
    customer.save()

    # Get the site URL for the email context
    site_url = get_site_url(request)  # Implement your get_site_url function

    # Prepare context for the email template
    context = {
        'user': customer,
        'site_url': site_url,
        'user_password': strong_password
    }

    # Send an email with the new account password
    email = Email()  # Instantiate your Email class
    email.send_mail(customer.email, 'email_templates/customer_password.html', context, 'Your New Account Password')

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



    common_get_response = {
    status.HTTP_200_OK: 
        docs_schema_response_new(
            status_code=status.HTTP_200_OK,
            serializer_class=serializer_class,
            message = "Data retrieved",
            )
    }
    
    @swagger_auto_schema(operation_id='Customer Listing', responses={**common_get_response})
    def get(self, request, *args, **kwargs):
        """
        Handle both AJAX (JSON) and HTML requests.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self,"customer", HasListDataPermission, 'list'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(created_by=request.user),
            "all": Q(),  # An empty Q() object returns all data
        }
        # Get the appropriate filter from the mapping based on the data access value,
        # or use an empty Q() object if the value is not in the mapping
        queryset = User.objects.filter(filter_mapping.get(data_access_value, Q()), roles__name__icontains='Customer').exclude(pk=request.user.id)
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

    @swagger_auto_schema(auto_schema=None) 
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

        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect
  
        contact_id = kwargs.get('contact_id')
        if contact_id:
            contact = Contact.objects.get(pk=contact_id)
            serializer = self.serializer_class(contact)  # Serialize the contact data
        else:
            serializer = self.serializer_class()  # Create an empty serializer

        if request.accepted_renderer.format == 'html':
            context = {'serializer':serializer}
            return render_html_response(context,self.template_name)
        else:
            return create_api_response(status_code=status.HTTP_201_CREATED,
                                message="GET Method Not Alloweded",)

    common_post_response = {
        status.HTTP_201_CREATED: 
            docs_schema_response_new(
                status_code=status.HTTP_201_CREATED,
                serializer_class=serializer_class,
                message = "Your customer has been added successfully.",
                ),
        status.HTTP_400_BAD_REQUEST: 
            docs_schema_response_new(
                status_code=status.HTTP_400_BAD_REQUEST,
                serializer_class=serializer_class,
                message = "We apologize for the inconvenience, but please review the below information.",
                ),

    } 

    @swagger_auto_schema(operation_id='Customer Add', responses={**common_post_response})
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to add or update a customer.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"customer", HasCreateDataPermission, 'add'
        )
        message = "Your customer has been added successfully."
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.save()
            
            create_customer(user, request)
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

    @swagger_auto_schema(auto_schema=None)
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
    
    common_post_response = {
        status.HTTP_200_OK: 
            docs_schema_response_new(
                status_code=status.HTTP_200_OK,
                serializer_class=serializer_class,
                message = "Your Customer has been updated successfully!",
                ),
        status.HTTP_400_BAD_REQUEST: 
            docs_schema_response_new(
                status_code=status.HTTP_400_BAD_REQUEST,
                serializer_class=serializer_class,
                message = "You are not authorized to perform this action",
                ),

    }

    @swagger_auto_schema(auto_schema=None) 
    def put(self, request, *args, **kwargs):
        pass

    @swagger_auto_schema(auto_schema=None) 
    def patch(self, request, *args, **kwargs):
        pass

    @swagger_auto_schema(operation_id='Customer Edit', responses={**common_post_response})
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
            data_dict = request.data.dict()
            data_dict['email'] = instance.email if instance else None
            serializer = self.serializer_class(instance = instance, data = data_dict, context = {'request': request} )
            if serializer.is_valid():
                # If the serializer data is valid, save the updated customer instance.
                serializer.save()
                message = "Your Customer has been updated successfully!"

                if request.accepted_renderer.format == 'html':
                    # For HTML requests, display a success message and redirect to contact_list.
                    messages.success(request, message)
                    return redirect(reverse('customer_edit', kwargs={'customer_id': kwargs['customer_id']}))

                else:
                    # For API requests, return a success response with serialized data.
                    return Response({'message': message, 'data': serializer.data}, status=status.HTTP_200_OK)
            else:
                if request.accepted_renderer.format == 'html':
                    # For HTML requests with invalid data, render the template with error messages.
                    context = {'serializer': serializer, 'customer_instance': instance}
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
    swagger_schema = None

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

    def get_billing_address_instance(self):
        
        
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "customer", HasUpdateDataPermission, 'change'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        filter_mapping = {
            "self": Q(user_id__created_by=self.request.user ),
            "all": Q(),  # An empty Q() object returns all data
        }
        
        billing_address = BillingAddress.objects.filter(filter_mapping.get(data_access_value, Q()))
        billing_address = billing_address.filter(user_id__id=self.kwargs.get('customer_id')).first()
        return billing_address

    def get(self, request, *args, **kwargs):
        """
        Handle GET request to display a form for updating a customer.
        If the customer exists, retrieve the serialized data and render the HTML template.
        If the customer does not exist, render the HTML template with an empty serializer.
        """
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
                messages.error(request, "You are not authorized to perform this action")
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
        
        
        billing_address = BillingAddress.objects.filter(filter_mapping.get(data_access_value, Q()))
        billing_address = billing_address.filter(user_id__id=self.kwargs.get('customer_id'),
                                                       pk=self.kwargs.get('address_id')).first()
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
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND, message=success_message )
        else:
            error_message= "Customer biling address not found OR You are not authorized to perform this action"
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
    
    common_delete_response = {
        status.HTTP_200_OK: 
            docs_schema_response_new(
                status_code=status.HTTP_200_OK,
                serializer_class=serializer_class,
                message = "Customer has been deleted successfully!",
                ),
        status.HTTP_404_NOT_FOUND: 
            docs_schema_response_new(
                status_code=status.HTTP_404_NOT_FOUND,
                serializer_class=serializer_class,
                message = "Customer not found OR You are not authorized to perform this action.",
                ),

    }
    @swagger_auto_schema(operation_id='Customer Delete', responses={**common_delete_response})
    
    def delete(self, request, *args, **kwargs):
        """
        Handle DELETE request to delete a customer.
        """
        # Get the customer instance from the database
        # Call the handle_unauthenticated method to handle unauthenticated access

        authenticated_user, data_access_value = check_authentication_and_permissions(
            self,"customer", HasDeleteDataPermission, 'delete'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(created_by=request.user ),
            "all": Q(),  # An empty Q() object returns all data
        }

        # Get the appropriate filter from the mapping based on the data access value,
        # or use an empty Q() object if the value is not in the mapping

        queryset = User.objects.filter(filter_mapping.get(data_access_value, Q()), pk=self.kwargs.get('pk'), roles__name__icontains='Customer').exclude(pk=request.user.id)
        
        customer = queryset.first()
        
        if customer:
            # Proceed with the deletion
            customer.delete()
            messages.success(request, "Customer has been deleted successfully!")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="Your Customer has been deleted successfully!", )
        else:
            messages.error(request, "Contact not found OR You are not authorized to perform this action.")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="Contact not found OR You are not authorized to perform this action.d", )

class CustomerDetailView(CustomAuthenticationMixin,generics.RetrieveAPIView):
    """
    View to get the listing of all contacts.
    Supports both HTML and JSON response formats.
    """
    serializer_class = CustomerSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    swagger_schema = None

    def get(self, request, *args, **kwargs):
        """
        Handle both AJAX (JSON) and HTML requests.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self,"requirement", HasCreateDataPermission, 'add'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        # Get the appropriate filter from the mapping based on the data access value,
        # or use an empty Q() object if the value is not in the mapping
        queryset = User.objects.filter(pk=self.kwargs.get('customer_id'), roles__name__icontains='Customer').exclude(pk=request.user.id).first()
        if queryset:
            site_address = SiteAddress.objects.filter(user_id__id=self.kwargs.get('customer_id'))
            site_data = []
            for site_address in site_address:
                site_data.append({
                    'id': site_address.id,
                    'site_name': site_address.site_name,
                })
            data = {
                'company_name': queryset.company_name,  # Replace with the actual field name
                'email': queryset.email,
                'first_name': queryset.first_name,
                'last_name': queryset.last_name,
                'site_address':site_data,
                
            }
        return create_api_response(status_code=status.HTTP_200_OK,
                                            message="Data retrieved",
                                            data=data)


class ConvertToCustomerView(CustomAuthenticationMixin,generics.CreateAPIView):
    """
    View to get the listing of all contacts.
    Supports both HTML and JSON response formats.
    """
    serializer_class = ContactCustomerSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    swagger_schema = None

    def get(self, request, *args, **kwargs):
        """
        Handle both AJAX (JSON) and HTML requests.
        """
        contact_id = kwargs.get('contact_id')
        if contact_id:
            contact = Contact.objects.get(pk=contact_id)
            
            data = {
                'email': contact.email,
                'first_name': contact.first_name,
                'last_name': contact.last_name,
                
                
            }
            
            serializer = self.serializer_class(data=data)  # Serialize the contact data
            # Check if the serialized data is valid
            if serializer.is_valid():
                customer = serializer.save()  # Save the serialized data and get the customer instance
                create_customer(customer, request)  # Create customer, assign role, generate password, and send email

                # Update customer details if available in the original contact data
                if contact.company_name:
                    customer.company_name = contact.company_name
                if contact.phone_number:
                    customer.phone_number = contact.phone_number

                customer.save()  # Save the updated customer details
                messages.success(request, 'The contact has been successfully converted into a customer.')
                return redirect(reverse('customer_edit', kwargs={'customer_id': customer.id}))
            else:
                # If serialized data is invalid, display error messages for each field
                for field, errors in serializer.errors.items():
                    error_message = f"{field.capitalize()}: {', '.join(errors)}"
                    messages.error(request, error_message)

            # Redirect back to the contact list page
            return redirect(reverse('contact_list'))
        
class BillingAddressInfoView(CustomAuthenticationMixin, APIView):
    """
    View to get the country county and town based on given post code query_params.
    """
    serializer_class = PostCodeInfoSerializer
    renderer_classes = [JSONRenderer]
    swagger_schema = None

    def get(self, request, *args, **kwargs):
        """
        Handle both AJAX (JSON) and HTML requests.
        """
        post_code = request.query_params.get('post_code')
        post_code_info = POST_CODES_INFO[post_code]
        data = {
            "post_code": post_code,
            "town": post_code_info[0] if post_code_info[0] else "Not Available",  # some towns are not available in post.
            "county": post_code_info[1],
            "country": post_code_info[2]
        }
        serialize = self.serializer_class(data=data)
        serialize.is_valid(raise_exception=True)
        return Response({"data": serialize.data})