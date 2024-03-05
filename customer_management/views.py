from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render, redirect
from django.http import Http404, JsonResponse, HttpResponse,HttpResponseBadRequest
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
from django.views import View
from django.http import HttpResponse
import csv
from .models import User, BillingAddress

from requirement_management.serializers import RequirementSerializer, RequirementQuotationListSerializer
from work_planning_management.serializers import Job, STWJobListSerializer, Job_STATUS_CHOICES

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

from invoice_management.serializers import (
    Invoice,
    InvoiceListSerializer,

    INVOICE_STATUS_CHOICES
)

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
    search_fields = ['company_name', ]
    template_name = 'customer_list.html'
    ordering_fields = ['created_at']
    queryset = CustomerMeta.objects.all()

    def get_paginated_queryset(self, base_queryset):
        items_per_page = 20 
        paginator = Paginator(base_queryset, items_per_page)
        page_number = self.request.GET.get('page')
        
        try:
            current_page = paginator.page(page_number)
        except PageNotAnInteger:
            # If page is not an integer, deliver the first page.
            current_page = paginator.page(1)
        except EmptyPage:
            # If page is out of range, deliver the last page of results.
            current_page = paginator.page(paginator.num_pages)
        
        return current_page
    
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = self.get_searched_queryset(queryset)
        queryset = self.get_paginated_queryset(queryset)
        return queryset

    def get_searched_queryset(self, queryset):
        search_params = self.request.query_params.get('q', '')
        if search_params:
            search_fields = self.search_fields
            q_objects = Q()

            # Construct a Q object to search across multiple fields dynamically
            for field in search_fields:
                q_objects |= Q(**{f'{field}__icontains': search_params})

            queryset = queryset.filter(q_objects)
        
        return queryset

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

        queryset = self.get_queryset()
        if request.accepted_renderer.format == 'html':
            context = {
                'customers': queryset,
                'search_fields': ['company name'],
                'search_value': request.query_params.get('q', '') if isinstance(request.query_params.get('q', []), str) else ', '.join(request.query_params.get('q', []))
            }
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
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect
            
        message = "Your customer has been added successfully."
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            customer = serializer.save()
            if request.accepted_renderer.format == 'html':
                messages.success(request, message)
                return redirect(reverse('customer_list'))
            else:
                # Return JSON response with success message and serialized data
                return create_api_response(status_code=status.HTTP_201_CREATED,
                    message=message,
                    data=serializer.data
                )
        if request.accepted_renderer.format == 'html':
            # Render the HTML template with invalid serializer data
            context = {'serializer':serializer}
            return render_html_response(context,self.template_name)
        else:   
            # Return JSON response with error message
            return create_api_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="We apologize for the inconvenience, but please review the below information.",
                data=convert_serializer_errors(serializer.errors)
        )

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
    queryset = User.objects.all()
    
    def get_queryset(self):
        """
        Get the queryset for listing Conatct items.

        Returns:
            QuerySet: A queryset of Conatct items filtered based on the authenticated user's ID.
        """
        pk = self.kwargs.get('customer_id', '')
        queryset = super().get_queryset()
        instance = None
        if pk and queryset:
            # Get the appropriate filter from the mapping based on the data access value,
            # or use an empty Q() object if the value is not in the mapping
            instance = queryset.filter(pk=pk).first()
        return instance

    @swagger_auto_schema(auto_schema=None)
    def get(self, request, *args, **kwargs):
        # Get the model class using the provided module_name string
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "customer", HasUpdateDataPermission, 'change'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        # This method handles GET requests for updating an existing Conatct object.
        if request.accepted_renderer.format == 'html':
            instance = self.get_queryset()
            company_meta = None
            try:
                company_meta = instance.customermeta
            except:
                messages.error(request, "You are not authorized to perform this action")
                return redirect(reverse('customer_list'))

            if instance and company_meta:
                serializer = self.serializer_class(instance=company_meta, context={'request': request})
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
       # Get the model class using the provided module_name string
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "customer", HasUpdateDataPermission, 'change'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect
        
        instance = self.get_queryset()
        company_meta = None
        try:
            company_meta = instance.customermeta
        except:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('customer_list'))

        if instance and not company_meta:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('customer_list'))
        
        # If the customer instance exists, initialize the serializer with instance and provided data.
        data = request.data.dict()
        serializer = self.serializer_class(instance = company_meta, data = data, context = {'request': request} )
        if serializer.is_valid():
            # If the serializer data is valid, save the updated customer instance.
            serializer.update(
                company_meta,
                serializer.validated_data
            )
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

class CustomerBillingAddressView(CustomAuthenticationMixin, generics.CreateAPIView):
    """
    View for adding or updating a customer.
    Supports both HTML and JSON response formats.
    """
    serializer_class = BillingAddressSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'customer_billing_address.html'
    swagger_schema = None
    queryset = BillingAddress.objects.all()

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
            queryset = queryset.filter(user_id=customer).first()
            return queryset
        return None
    
    def get(self, request, *args, **kwargs):
        """
        Handle GET request to display a form for updating a customer.
        If the customer exists, retrieve the serialized data and render the HTML template.
        If the customer does not exist, render the HTML template with an empty serializer.
        """
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "customer", HasUpdateDataPermission, 'change'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        customer = self.get_customer()
        if not customer:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('customer_list'))

        instance = self.get_queryset(customer)
        serializer = self.serializer_class(instance=instance) if instance else self.serializer_class()
        if request.accepted_renderer.format == 'html':
            context = {
                'serializer': serializer, 
                'customer_instance': customer,
            }
            return render_html_response(context,self.template_name)
        else:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('customer_list'))

    def post(self, request, *args, **kwargs):
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "customer", HasUpdateDataPermission, 'change'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        customer = self.get_customer()
        if not customer:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('customer_list'))

        instance = self.get_queryset(customer)

        serializer = self.serializer_class(data=request.data, instance=instance, context={'request': request}) if instance else self.serializer_class(data=request.data, context={'request': request})
        message = f"Your Customer billing address has been {'updated' if instance else 'added'} successfully!"

        if serializer.is_valid():
            serializer.validated_data['user_id'] = customer
            # If the serializer data is valid, save the billing address instance.
            serializer.update(instance=instance, validated_data=serializer.validated_data) if instance else serializer.save()

            if request.accepted_renderer.format == 'html':
                # For HTML requests, display a success message and redirect to the customer's billing address list.
                messages.success(request, message)
                return redirect(reverse('customer_billing_address', kwargs={'customer_id': kwargs['customer_id']}))
            else:
                # For API requests, return a success response with serialized data.
                return create_api_response(message=message, data=serializer.data, status=status.HTTP_200_OK)
        else:
            message = "Unable to submit your data please validate and try again."
            if request.accepted_renderer.format == 'html':
                # For HTML requests with invalid data, render the template with error messages.
                context = {
                    'serializer': serializer,
                    'customer_instance': customer,
                }
                return render(request, self.template_name, context)
            else:
                # For API requests with invalid data, return an error response with serializer errors.
                return create_api_response(message=message, data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
    queryset = User.objects.filter(is_active=False).all()
    
    def get_queryset(self):
        """
        Get the queryset for listing Conatct items.

        Returns:
            QuerySet: A queryset of Conatct items filtered based on the authenticated user's ID.
        """
        pk = self.kwargs.get('pk', '')
        queryset = super().get_queryset()
        instance = None
        if pk and queryset:
            # Get the appropriate filter from the mapping based on the data access value,
            # or use an empty Q() object if the value is not in the mapping
            instance = queryset.filter(pk=pk).first()
        return instance
    
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

        customer = self.get_queryset()
        if customer:
            # Proceed with the deletion
            contacts = ContactPerson.objects.filter(customer=customer.customermeta).all()
            contacts.delete()
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
    queryset = Contact.objects.all()

    def get_object(self) -> Contact:
        queryset = super().get_queryset()
        contact_id = self.kwargs.get('contact_id')

        if queryset and contact_id:
            instance = queryset.filter(id=contact_id, contact_type__name__icontains='prospect').first()
            return instance

        return None


    def get(self, request, *args, **kwargs):
        """
        Handle both AJAX (JSON) and HTML requests.
        """
        instance = self.get_object()
        if not instance:
            messages.error(request, 'You are not authorised to perform this action.')
            return redirect(reverse('contact_list'))

        if CustomerMeta.objects.filter(company_name=instance.company_name).exists():
            messages.error(request, 'You cannot convert the Contact into Customer as a Customer with this company name is already present.')
            return redirect(reverse('contact_list'))
        
        data = {
            'company_name': instance.company_name, 
            'company_registration_number': f'IFP-C-{CustomerMeta.objects.count()+1}',
            'registered_address': instance.address, 
            'registered_town': instance.town, 
            'registered_county': instance.county, 
            'registered_country': instance.country,  
            'registered_post_code': instance.post_code,
            'email': instance.email, 
            'main_telephone_number': instance.phone_number
        }

        user_data = {
            'first_name': instance.first_name, 
            'last_name': instance.last_name, 
            'email': instance.email, 
            'phone_number': instance.phone_number,
            'job_role': instance.job_title,
            'is_active': True
        }

        serializer = self.get_serializer(
            data = data
        )

        if serializer.is_valid():
            customer = serializer.save()

            contact_serializer = ContactPersonSerializer(data=user_data)
            if contact_serializer.is_valid():
                contact_serializer.validated_data['customer'] = customer
                contact_serializer.save()
                messages.success(request, 'The contact has been successfully converted into a customer.')
                return redirect(reverse('customer_edit', kwargs={'customer_id': customer.user_id.id}))
            
            else:
                customer.delete()
                # If serialized data is invalid, display error messages for each field
                errors = [ f"{', '.join(errors)}" for field, errors in serializer.errors.items() ]
                error_message = f"{', '.join(errors)}"
                messages.error(request, error_message)
        else:
            # If serialized data is invalid, display error messages for each field
            errors = [ f"{', '.join(errors)}" for field, errors in serializer.errors.items() ]
            error_message = f"{', '.join(errors)}"
            messages.error(request, error_message)

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

class ExportCSVView(View):
    def get(self, request, *args, **kwargs):
        stw_ids = request.GET.get('stw_ids', '')
        if not stw_ids:
            messages.error(request, 'No Row was selected to export the data, Please selecte a row and try again.')
            return redirect('customer_list')
        
        selected_ids = stw_ids.split(',') if stw_ids else []
        stw_ids = [int(id_) for id_ in selected_ids if id_.isdigit()]

        # Fetch data efficiently using select_related
        user_data = User.objects.filter(id__in=stw_ids).select_related('billingaddress').values(
            'id', 'first_name', 'last_name', 'email', 'company_name', 'customer_type', 'phone_number',
            'billingaddress__vat_number', 'billingaddress__tax_preference', 'billingaddress__address', 'billingaddress__country',
            'billingaddress__town', 'billingaddress__county', 'billingaddress__post_code'
        )

        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="exported_data.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'id', 'first_name', 'last_name', 'email', 'company_name', 'customer_type', 'phone_number',
            'vat_number_billing', 'tax_preference_billing', 'address_billing', 'country_billing',
            'town_billing', 'county_billing', 'post_code_billing'
        ])

        for row in user_data:
            writer.writerow([row[field] for field in row])  # Write all fields, handling potential None values

        return response

class CMRequirementListView(CustomAuthenticationMixin,generics.ListAPIView):
    """
    View to get the listing of all requirements.
    Supports both HTML and JSON response formats.
    """
    serializer_class = RequirementSerializer
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    filter_backends = [filters.SearchFilter]
    search_fields = ['action', 'description']
    template_name = 'customer_fra_list.html'
    ordering_fields = ['created_at'] 
    queryset = Requirement.objects.all()

    common_get_response = {
    status.HTTP_200_OK: 
        docs_schema_response_new(
            status_code=status.HTTP_200_OK,
            serializer_class=serializer_class,
            message = "Data retrieved",
            )
    }

    def get_filter_queryset(self, queryset):
        filters = {
            'status': self.request.GET.get('status'),
            'surveyor': self.request.GET.get('surveyor'),
            'dateRange': self.request.GET.get('dateRange'),
        }
        date_format = '%d/%m/%Y'

        # Apply additional filters based on the received parameters
        for filter_name, filter_value in filters.items():
            if filter_value:
                if filter_name == 'dateRange':
                    # If 'dateRange' parameter is provided, filter TODO items within the date range
                    start_date_str, end_date_str = filter_value.split('-')
                    start_date = datetime.strptime(start_date_str.strip(), date_format).date()
                    end_date = datetime.strptime(end_date_str.strip(), date_format).date()
                    queryset = queryset.filter(due_date__gte=start_date, due_date__lte=end_date)
                elif filter_name == 'surveyor':
                    value_list = filter_value.split()
                    if 2 >= len(value_list) > 1:
                        queryset = queryset.filter(surveyor__first_name=value_list[0], surveyor__last_name=value_list[1])
                    else:
                        queryset = queryset.filter(surveyor__first_name = filter_value)
                else:
                    # For other filters, apply the corresponding filters on the queryset
                    filter_mapping = {
                        'status': 'status',
                    }
                    queryset = queryset.filter(**{filter_mapping[filter_name]: filter_value.strip()})
        
        return queryset

    def get_queryset(self, customer_data):
        queryset = super().get_queryset()
        if not customer_data:
            return []

        queryset = queryset.filter(customer_id=customer_data).all()
        return queryset

    def get_searched_queryset(self, queryset):
        search_params = self.request.query_params.get('q', '')
        if search_params:
            search_fields = self.search_fields
            q_objects = Q()

            # Construct a Q object to search across multiple fields dynamically
            for field in search_fields:
                q_objects |= Q(**{f'{field}__icontains': search_params})

            queryset = queryset.filter(q_objects)
        
        return queryset
    
    @swagger_auto_schema(operation_id='Requirement Listing', responses={**common_get_response})
    def get(self, request, *args, **kwargs):

        """
        Handle both AJAX (JSON) and HTML requests.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access.
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self,"fire_risk_assessment", HasListDataPermission, 'list'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect
        
        customer_id = kwargs.get('customer_id', None)
        customer_data = User.objects.filter(id=customer_id).first()
        if customer_data:
            queryset = self.get_queryset(customer_data)
            queryset = self.get_filter_queryset(queryset)
            queryset = self.get_searched_queryset(queryset)
            # qs_role = UserRole.objects.filter(name='quantity_surveyor')
            # quantity_sureveyors = User.objects.filter(roles__in=qs_role)
            
            sureveyors = User.objects.filter(roles__name='surveyor')

            
            if request.accepted_renderer.format == 'html':
                page_number = request.GET.get('page', 1)
                context = {
                    'requirements': Paginator(self.serializer_class(queryset, many=True).data, 20).get_page(page_number),
                    'customer_id':customer_id,
                    'customer_instance':customer_data,
                    'sureveyors':sureveyors,
                    'status_values': REQUIREMENT_CHOICES,
                    'search_fields': self.search_fields,
                    'search_value': request.query_params.get('q', '') if isinstance(request.query_params.get('q', []), str) else ', '.join(request.query_params.get('q', [])),
                }
                return render_html_response(context,self.template_name)
            else:
                serializer = self.serializer_class(queryset, many=True)
                return create_api_response(status_code=status.HTTP_200_OK,
                                                message="Data retrieved",
                                                data=serializer.data)
        else:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('customer_requirement_list', kwargs={'customer_id': customer_id}))  
        

class CMJobsListView(CustomAuthenticationMixin, generics.ListAPIView):
    serializer_class = STWJobListSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    filter_backends = [filters.SearchFilter]
    search_fields = ['assigned_to_team__members__name', 'assigned_to_member__name']
    template_name = 'customer_job_list.html'
    ordering_fields = ['created_at']
    queryset = Job.objects.all()

    common_get_response = {
        status.HTTP_200_OK: docs_schema_response_new(
            status_code=status.HTTP_200_OK,
            serializer_class=serializer_class,
            message="Data retrieved",
        )
    }

    def get_filtered_queryset(self, queryset):
        # Get the filtering parameters from the request's query parameters
        filters = {
            'status': self.request.GET.get('status'),
            'dateRange': self.request.GET.get('dateRange'),
        }
        date_format = '%d/%m/%Y'

        # Apply additional filters based on the received parameters
        for filter_name, filter_value in filters.items():
            if filter_value:
                if filter_name == 'dateRange':
                    # If 'dateRange' parameter is provided, filter TODO items within the date range
                    start_date_str, end_date_str = filter_value.split('-')
                    start_date = datetime.strptime(start_date_str.strip(), date_format).date()
                    end_date = datetime.strptime(end_date_str.strip(), date_format).date()
                    queryset = queryset.filter(
                        Q(start_date__date__gte=start_date, start_date__date__lte=end_date) |
                        Q(end_date__date__lte=end_date, end_date__date__gte=start_date)
                    )
                else:
                    # For other filters, apply the corresponding filters on the queryset
                    filter_mapping = {
                        'status': 'status',
                    }
                    queryset = queryset.filter(**{filter_mapping[filter_name]: filter_value.strip()})
        
        return queryset

    def get_paginated_queryset(self, base_queryset):
        items_per_page = 20 
        paginator = Paginator(base_queryset, items_per_page)
        page_number = self.request.GET.get('page')
        
        try:
            current_page = paginator.page(page_number)
        except PageNotAnInteger:
            # If page is not an integer, deliver the first page.
            current_page = paginator.page(1)
        except EmptyPage:
            # If page is out of range, deliver the last page of results.
            current_page = paginator.page(paginator.num_pages)
        
        return current_page
    
    def get_searched_queryset(self, queryset):
        search_params = self.request.query_params.get('q', '')
        if search_params:
            search_fields = self.search_fields
            q_objects = Q()

            # Construct a Q object to search across multiple fields dynamically
            for field in search_fields:
                q_objects |= Q(**{f'{field}__icontains': search_params})

            queryset = queryset.filter(q_objects)
        
        return queryset

    def get_queryset(self, data_access_value, customer_data):
        """
        Get the queryset based on filtering parameters from the request.
        """
        from django.db.models import F
        queryset = super().get_queryset()
        filter_mapping = {
            "self": Q(user_id=self.request.user),
            "all": Q(),
        }
        queryset = queryset.filter(filter_mapping.get(data_access_value, Q())).distinct()
        
        queryset = queryset.filter(customer_id=customer_data).all()
        # Order the queryset based on the 'ordering_fields'
        ordering = self.request.GET.get('ordering')
        if ordering in self.ordering_fields:
            queryset = queryset.order_by(ordering)

        queryset = self.get_filtered_queryset(queryset)
        queryset = self.get_searched_queryset(queryset.order_by('-created_at'))
        queryset = self.get_paginated_queryset(queryset)

        return queryset

    @swagger_auto_schema(operation_id='STW Job Assignment Listing', responses={**common_get_response})
    def get(self, request, *args, **kwargs):
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasListDataPermission, 'list'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user

        customer_id = kwargs.get('customer_id', None)
        customer_data = User.objects.filter(id=customer_id).first()

        if customer_data:
            queryset = self.get_queryset(data_access_value, customer_data)

            if request.accepted_renderer.format == 'html':
                context = {
                    'jobs': queryset,
                    'customer_instance': customer_data,
                    'status_values': Job_STATUS_CHOICES,
                    'search_fields': self.search_fields,
                    'search_value': request.query_params.get('q', '') if isinstance(request.query_params.get('q', []), str) else ', '.join(request.query_params.get('q', [])),
                }
                return render_html_response(context, self.template_name)
            else:
                serializer = self.serializer_class(queryset, many=True)
                return create_api_response(status_code=status.HTTP_200_OK,
                                           message="Data retrieved",
                                           data=serializer.data)
        else:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('job_customers_list'))

class CMQuotationListView(CustomAuthenticationMixin,generics.ListAPIView):
    
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    filter_backends = [filters.SearchFilter]
    search_fields = ['requirement_id__action', 'requirement_id__description', 'requirement_id__UPRN']
    template_name = 'customer_quote_list.html'
    ordering_fields = ['created_at'] 
    serializer_class = RequirementQuotationListSerializer

    def get_paginated_queryset(self, base_queryset):
        items_per_page = 20 
        paginator = Paginator(base_queryset, items_per_page)
        page_number = self.request.GET.get('page')
        
        try:
            current_page = paginator.page(page_number)
        except PageNotAnInteger:
            # If page is not an integer, deliver the first page.
            current_page = paginator.page(1)
        except EmptyPage:
            # If page is out of range, deliver the last page of results.
            current_page = paginator.page(paginator.num_pages)
        
        return current_page
    
    def get_searched_queryset(self, queryset):
        search_params = self.request.query_params.get('q', '')
        if search_params:
            search_fields = self.search_fields
            q_objects = Q()

            # Construct a Q object to search across multiple fields dynamically
            for field in search_fields:
                q_objects |= Q(**{f'{field}__icontains': search_params})

            queryset = queryset.filter(q_objects)
        
        return queryset

    def get_filtered_queryset(self, queryset):
        # Get the filtering parameters from the request's query parameters
        filters = {
            'surveyor': self.request.GET.get('surveyor'),
            'status': self.request.GET.get('status'),
        }

        # Apply additional filters based on the received parameters
        for filter_name, filter_value in filters.items():
            if filter_value:
                if filter_name == 'surveyor':
                    value_list = filter_value.split()
                    if 2 >= len(value_list) > 1:
                        queryset = queryset.filter(requirement_id__surveyor__first_name=value_list[0], requirement_id__surveyor__last_name=value_list[1])
                    else:
                        queryset = queryset.filter(requirement_id__surveyor__first_name = filter_value)
                else:
                    # For other filters, apply the corresponding filters on the queryset
                    filter_mapping = {
                        'status': 'status',
                    }
                    queryset = queryset.filter(**{filter_mapping[filter_name]: filter_value.strip()})
                    
        
        return self.get_searched_queryset(queryset)

    def get_queryset(self):
        queryset = Quotation.objects.filter(requirement_id__customer_id=self.kwargs.get('customer_id'))
        return self.get_filtered_queryset(queryset)

    def get(self, request, *args, **kwargs):
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "fire_risk_assessment", HasListDataPermission, 'list'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        customer_id = kwargs.get('customer_id')
        customer_data = User.objects.filter(id=customer_id).first()

        if customer_data:
            queryset = self.get_queryset()
           
            if request.accepted_renderer.format == 'html':
                context = {'quotation_list': self.get_paginated_queryset(self.serializer_class(queryset, many=True).data),
                'customer_id': customer_id,
                'customer_instance':customer_data,
                'status_values': QUOTATION_STATUS_CHOICES,
                'search_fields': self.search_fields,
                'search_value': request.query_params.get('q', '') if isinstance(request.query_params.get('q', []), str) else ', '.join(request.query_params.get('q', []))}  # Pass the list of customers with counts to the template
                return render_html_response(context, self.template_name)
        else:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('view_customer_list_quotation'))

class CMInvoiceListView(CustomAuthenticationMixin,generics.ListAPIView):
    
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    filter_backends = [filters.SearchFilter]
    search_fields = ['requirement__action', 'requirement__description', 'requirement__UPRN']
    template_name = 'customer_invoice_list.html'
    ordering_fields = ['created_at'] 
    serializer_class = InvoiceListSerializer

    def get_paginated_queryset(self, base_queryset):
        items_per_page = 20 
        paginator = Paginator(base_queryset, items_per_page)
        page_number = self.request.GET.get('page')
        
        try:
            current_page = paginator.page(page_number)
        except PageNotAnInteger:
            # If page is not an integer, deliver the first page.
            current_page = paginator.page(1)
        except EmptyPage:
            # If page is out of range, deliver the last page of results.
            current_page = paginator.page(paginator.num_pages)
        
        return current_page
    
    def get_searched_queryset(self, queryset):
        search_params = self.request.query_params.get('q', '')
        if search_params:
            search_fields = self.search_fields
            q_objects = Q()

            # Construct a Q object to search across multiple fields dynamically
            for field in search_fields:
                q_objects |= Q(**{f'{field}__icontains': search_params})

            queryset = queryset.filter(q_objects)
        
        return queryset

    def get_filtered_queryset(self, queryset):
        filters = {
            'status': self.request.GET.get('status'),
            'surveyor': self.request.GET.get('surveyor'),
            'dateRange': self.request.GET.get('dateRange'),
        }
        date_format = '%d/%m/%Y'

        # Apply additional filters based on the received parameters
        for filter_name, filter_value in filters.items():
            if filter_value:
                if filter_name == 'dateRange':
                    # If 'dateRange' parameter is provided, filter TODO items within the date range
                    start_date_str, end_date_str = filter_value.split('-')
                    start_date = datetime.strptime(start_date_str.strip(), date_format).date()
                    end_date = datetime.strptime(end_date_str.strip(), date_format).date()
                    queryset = queryset.filter(Q(submitted_at__isnull=False) | Q(paid_at__isnull=False))
                    queryset = queryset.filter(Q(submitted_at__date__gte=start_date, submitted_at__date__lte=end_date) | Q(paid_at__date__gte=start_date, paid_at__date__lte=end_date))
                elif filter_name == 'surveyor':
                    value_list = filter_value.split()
                    if 2 >= len(value_list) > 1:
                        queryset = queryset.filter(requirement__surveyor__first_name=value_list[0], requirement__surveyor__last_name=value_list[1])
                    else:
                        queryset = queryset.filter(requirement__surveyor__first_name = filter_value)
                else:
                    # For other filters, apply the corresponding filters on the queryset
                    filter_mapping = {
                        'status': 'status',
                    }
                    queryset = queryset.filter(**{filter_mapping[filter_name]: filter_value.strip()})
        
        return self.get_searched_queryset(queryset)

    def get_queryset(self):
        queryset = Invoice.objects.filter(customer=self.kwargs.get('customer_id'))
        return self.get_filtered_queryset(queryset)

    def get(self, request, *args, **kwargs):
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "fire_risk_assessment", HasListDataPermission, 'list'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        customer_id = kwargs.get('customer_id')
        customer_data = User.objects.filter(id=customer_id).first()

        if customer_data:
            queryset = self.get_queryset()
           
            if request.accepted_renderer.format == 'html':
                context = {
                    'invoice_list': self.get_paginated_queryset(self.serializer_class(queryset, many=True).data),
                    'customer_id': customer_id,
                    'customer_instance': customer_data,
                    'status_values': INVOICE_STATUS_CHOICES,
                    'search_fields': self.search_fields,
                    'search_value': request.query_params.get('q', '') if isinstance(request.query_params.get('q', []), str) else ', '.join(request.query_params.get('q', []))
                }  # Pass the list of customers with counts to the template
                return render_html_response(context, self.template_name)
        else:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('view_customer_list_quotation'))
