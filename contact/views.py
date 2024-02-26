from django.core.paginator import Paginator
from django.contrib import messages
from django.urls import reverse
from django.shortcuts import render, redirect
from django.http import Http404, JsonResponse, HttpResponse
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema

from infinity_fire_solutions.aws_helper import *
from infinity_fire_solutions.permission import *
from .models import *
from .serializers import ContactSerializer, ConversationSerializer, ConversationViewSerializer
from infinity_fire_solutions.response_schemas import create_api_response, convert_serializer_errors, render_html_response

from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from django.http import HttpResponseRedirect
from infinity_fire_solutions.utils import docs_schema_response_new
from django.views import View
import csv
from django.utils.encoding import smart_str




class ContacttypeAutocomplete(View):
    def get(self, request):
        query = request.GET.get('term', '')
        contact_types = ContactType.objects.filter(Q(name__icontains=query))[:10]
        # Create a list of dictionaries containing both name and primary key
        results = [{'label': type.name, 'value': type.id} for type in contact_types]
        return JsonResponse(results, safe=False)

class SubContractorSearchAPIView(CustomAuthenticationMixin, generics.RetrieveAPIView):
    """
    API view for searching SubContractors based on a search term.

    This view allows searching for SubContractors by their first name, last name, or email.

    Parameters:
    - CustomAuthenticationMixin: Custom authentication mixin for handling authentication.
    - RetrieveAPIView: A generic view for retrieving data.

    Attributes:
    - renderer_classes: List of renderer classes for rendering the API response.
    - swagger_schema: Swagger schema for API documentation.
    - template_name: HTML template for rendering the response.

    Methods:
    - get: Handles GET requests for searching SubContractors.
    """

    renderer_classes = [JSONRenderer]
    swagger_schema = None

    def get(self, request, *args, **kwargs):
        """
        Handle GET requests for searching SubContractors.

        Args:
        - request: The HTTP request object.
        - *args: Additional positional arguments.
        - **kwargs: Additional keyword arguments.

        Returns:
        - Response: The API response containing the search results.
        """
        # Get the search term from the query parameter
        search_term = request.GET.get('term')
        data = {}

        if search_term:
            # Filter vendors based on the search term
            sub_contractor_list = Contact.objects.filter(
                Q(first_name__icontains=search_term, contact_type__name__icontains="Sub-Contractor") |
                Q(last_name__icontains=search_term, contact_type__name__icontains="Sub-Contractor") |
                Q(email__icontains=search_term, contact_type__name__icontains="Sub-Contractor")
            )

            # Get the email from the vendor list
            results = [user.email for user in sub_contractor_list]

            data = {'results': results}

        # Create an API response
        return create_api_response(
            status_code=status.HTTP_200_OK,
            message="SubContractor data",
            data=data
        )


class ContactListView(CustomAuthenticationMixin,generics.ListAPIView):
    """
    View to get the listing of all contacts.
    Supports both HTML and JSON response formats.
    """
    serializer_class = ContactSerializer
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    filter_backends = [filters.SearchFilter]
    search_fields = ['first_name', 'last_name','email']
    template_name = 'contact_list.html'
    ordering_fields = ['created_at'] 


    
    def get_queryset(self):
        """
        Get the queryset based on filtering parameters from the request.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "contact", HasListDataPermission, 'list'
        )
        # Check if authenticated_user is a redirect response
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        
        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(user_id=self.request.user),
            "all": Q(),  # An empty Q() object returns all data
        }
        # Get the appropriate filter from the mapping based on the data access value,
        # or use an empty Q() object if the value is not in the mapping
        base_queryset = Contact.objects.filter(filter_mapping.get(data_access_value, Q())).distinct().order_by('-created_at')
        
        # Get the filtering parameters from the request's query parameters
        contact_type_filter = self.request.GET.get('contact_type')

        # Apply additional filters based on the received parameters
        if contact_type_filter:
            # If 'contact_type' parameter is provided, filter contacts by the given contact_type
            base_queryset = base_queryset.filter(contact_type__name=contact_type_filter)

        # Add more filtering conditions as needed for other fields

        # Order the queryset based on the 'ordering_fields'
        ordering = self.request.GET.get('ordering')
        if ordering in self.ordering_fields:
            base_queryset = base_queryset.order_by(ordering)

        return base_queryset
    

    def get_contact_types(self):
        """
        Get a list of all contact types.
        """
        return ContactType.objects.all()
    
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

    @swagger_auto_schema(operation_id='Contact Listing', responses={**common_get_response}) 
    def get(self, request, *args, **kwargs):
        """
        Handle both AJAX (JSON) and HTML requests.
        """
        # Get the filtered queryset using get_queryset method
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "contact", HasListDataPermission, 'list'
        )
        # Check if authenticated_user is a redirect response
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        queryset = self.get_queryset()
        contact_types = self.get_contact_types()
        contact_type_filter = self.request.GET.get('contact_type', '')
        if request.accepted_renderer.format == 'html':
            queryset = self.get_searched_queryset(queryset)
            page_number = request.GET.get('page', 1)
            context = {'contacts': Paginator(queryset, 20).get_page(page_number),
                       'contact_types': contact_types,
                       'search_fields': ['name', 'email'],
                       'search_value': request.query_params.get('q', '') if isinstance(request.query_params.get('q', []), str) else ', '.join(request.query_params.get('q', [])),
                       'contact_type_filter':contact_type_filter}
            return render_html_response(context, self.template_name)
        else:
            serializer = self.serializer_class(queryset, many=True)
            return create_api_response(
                status_code=status.HTTP_200_OK,
                message="Data retrieved",
                data=serializer.data
            )
    
    
class ContactAddView(CustomAuthenticationMixin, generics.CreateAPIView):
    """
    View for adding or updating a contact.
    Supports both HTML and JSON response formats.
    """
    serializer_class = ContactSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'contact.html'

    
    def get_queryset(self):
        """
        Get the filtered queryset for contacts based on the authenticated user.
        """
        queryset = Contact.objects.filter(pk=self.kwargs.get('pk'),user_id=self.request.user.id).order_by('-created_at').first()
        return queryset

    @swagger_auto_schema(auto_schema=None) 
    def get(self, request, *args, **kwargs):
        """
        Handle GET request to display a form for updating a contact.
        If the contact exists, retrieve the serialized data and render the HTML template.
        If the contact does not exist, render the HTML template with an empty serializer.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"contact", HasCreateDataPermission, 'add'
        )
        
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect


        if request.accepted_renderer.format == 'html':
            context = {'serializer':self.serializer_class()}
            return render_html_response(context,self.template_name)
        else:
            return create_api_response(status_code=status.HTTP_201_CREATED,
                                message="GET Method Not Alloweded",)

    common_post_response = {
        status.HTTP_200_OK: 
            docs_schema_response_new(
                status_code=status.HTTP_200_OK,
                serializer_class=serializer_class,
                message = "your contact has been added successfully.",
                ),
        status.HTTP_400_BAD_REQUEST: 
            docs_schema_response_new(
                status_code=status.HTTP_400_BAD_REQUEST,
                serializer_class=serializer_class,
                message = "We apologize for the inconvenience, but please review the below information.",
                ),

    }  

    @swagger_auto_schema(operation_id='Contact Add', responses={**common_post_response})
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to add or update a contact.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"contact", HasCreateDataPermission, 'add'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect
        
        # Check if 'contact_type' is empty in the request data
        if not request.data.get('contact_type'):
            # Create the serializer instance without saving it to the database
            serializer = self.serializer_class(data=request.data)

            # Check if the serializer is valid before accessing .data
            if serializer.is_valid():
                context = {'serializer': serializer}
            else:
                context = {'serializer': serializer, 'error_message': "Invalid data. Please review the below information."}

            return render_html_response(context, self.template_name)


        message = "your contact has been added successfully."
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            # Use the provided contact_type_id to set the contact_type field
            contact = serializer.save(user_id=request.user)
            contact.save()

            if request.accepted_renderer.format == 'html':
                messages.success(request, message)
                return redirect(reverse('contact_list'))

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
            


class ContactUpdateView(CustomAuthenticationMixin, generics.UpdateAPIView):
    """
    API view for updating a contact.

    This view handles both HTML and API requests for updating a contact instance.
    If the contact instance exists, it will be updated with the provided data.
    Otherwise, an error message will be returned.

    The following request methods are supported:
    - POST: Updates the contact instance.

    Note: Make sure to replace 'your_template_name.html' with the appropriate HTML template name.
    """
    
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'contact.html'
    serializer_class = ContactSerializer

    
    def get_queryset(self):
        """
        Get the queryset for listing Conatct items.

        Returns:
            QuerySet: A queryset of Conatct items filtered based on the authenticated user's ID.
        """
        # Get the model class using the provided module_name string
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "contact", HasUpdateDataPermission, 'change'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(user_id=self.request.user ),
            "all": Q(),  # An empty Q() object returns all data
        }

        # Get the appropriate filter from the mapping based on the data access value,
        # or use an empty Q() object if the value is not in the mapping
        queryset = Contact.objects.filter(filter_mapping.get(data_access_value, Q())).distinct().order_by('-created_at')
        queryset = queryset.filter(pk=self.kwargs.get('pk')).first()
        
        return queryset

    @swagger_auto_schema(auto_schema=None)
    def get(self, request, *args, **kwargs):
        # This method handles GET requests for updating an existing Conatct object.
        if request.accepted_renderer.format == 'html':
            instance = self.get_queryset()
            if instance:
                serializer = self.serializer_class(instance=instance, context={'request': request})

                # Add the serialized data to the context
                context = {'serializer': serializer, 'instance': instance}
                return render_html_response(context, self.template_name)
            else:
                messages.error(request, "You are not authorized to perform this action")
                return redirect(reverse('contact_list'))
            
    common_put_response = {
        status.HTTP_200_OK: 
            docs_schema_response_new(
                status_code=status.HTTP_200_OK,
                serializer_class=serializer_class,
                message = "Your Contact has been updated successfully!",
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

    @swagger_auto_schema(operation_id='Contact Edit', responses={**common_put_response})
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to update a contact instance.

        Args:
            request (rest_framework.request.Request): The HTTP request object.
            *args: Variable-length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            rest_framework.response.Response: HTTP response object.
                If successful, the contact is updated, and the appropriate response is returned.
                If unsuccessful, an error response is returned.
        """
        data = request.data
        instance = self.get_queryset()
        if instance:
            # If the contact instance exists, initialize the serializer with instance and provided data.
            serializer = self.serializer_class(instance=instance, data=data)
            print(data,"data")
            if serializer.is_valid():
                contact_type_id = request.data.get('id_contact_type')

            # If contact_type_id is provided, fetch the corresponding object
                if contact_type_id:
                    try:
                        contact_type_obj = ContactType.objects.get(id=contact_type_id)
                        serializer.validated_data['contact_type'] = contact_type_obj  # Assign the object to serializer data
                    except ContactType.DoesNotExist:
                        serializer.errors['contact_type'] = "Invalid contact type"  # Add error message if not found
                # If the serializer data is valid, save the updated contact instance.
                serializer.save()
                message = "Your Contact has been updated successfully!"

                if request.accepted_renderer.format == 'html':
                    # For HTML requests, display a success message and redirect to contact_list.
                    messages.success(request, message)
                    return redirect('contact_list')
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
                return redirect('contact_list')
            else:
                # For API requests with no instance, return an error response with an error message.
                return Response({'message': error_message}, status=status.HTTP_400_BAD_REQUEST)

                         
class ContactDeleteView(CustomAuthenticationMixin, generics.DestroyAPIView):
    """
    View for updating a contact.
    Supports both HTML and JSON response formats.
    """
    serializer_class = ContactSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    # permission_classes = [IsAuthenticated]
    template_name = 'contact.html'
    

    common_delete_response = {
        status.HTTP_200_OK: 
            docs_schema_response_new(
                status_code=status.HTTP_200_OK,
                serializer_class=serializer_class,
                message = "Your contact has been deleted successfully!",
                ),
        status.HTTP_404_NOT_FOUND: 
            docs_schema_response_new(
                status_code=status.HTTP_404_NOT_FOUND,
                serializer_class=serializer_class,
                message = "Contact not found OR You are not authorized to perform this action.",
                ),

    }
    @swagger_auto_schema(operation_id='Contact Delete', responses={**common_delete_response})
    def delete(self, request, *args, **kwargs):
        """
        Handle DELETE request to delete a contact.
        """
        # Get the contact instance from the database
         # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self,"contact", HasDeleteDataPermission, 'delete'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(user_id=request.user ),
            "all": Q(),  # An empty Q() object returns all data
        }

        # Get the appropriate filter from the mapping based on the data access value,
        # or use an empty Q() object if the value is not in the mapping
        queryset = Contact.objects.filter(filter_mapping.get(data_access_value, Q()))
        instance = queryset.filter(pk=self.kwargs.get('pk')).first()
        if instance:
            # Proceed with the deletion
            instance.delete()
            messages.success(request, "Your contact has been deleted successfully!")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="Your contact has been deleted successfully!", )
        else:
            messages.error(request, "Contact not found OR You are not authorized to perform this action.")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="Contact not found OR You are not authorized to perform this action.", )
                   
class ConversationView(CustomAuthenticationMixin, generics.RetrieveAPIView):
    """
    View to display and manage conversations related to a contact.
    """
    serializer_class = ConversationSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'conversation.html'
    filter_backends = [filters.SearchFilter]
    search_fields = ['title']
    ordering_fields = ['created_at'] 
    swagger_schema = None
    
    
    def get_queryset(self,*args, **kwargs):
        """
        Get the queryset of contacts filtered by the current user.
        """
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self,"contact", HasViewDataPermission, 'view'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(user_id=self.request.user ),
            "all": Q(),  # An empty Q() object returns all data
        }
        
        # Get the appropriate filter from the mapping based on the data access value,
        # or use an empty Q() object if the value is not in the mapping
        queryset = Contact.objects.filter(filter_mapping.get(data_access_value, Q()))
        queryset = queryset.filter(pk=self.kwargs.get('contact_id')).first()
        return queryset
    

    def get_conversation_queryset(self):
        """
        Get the queryset of conversations filtered by the current user.
        """
        return Conversation.objects.filter(user_id=self.request.user)
    

    def get_conversation_types(self):
        """
        Get a list of all contact types.
        """
        return ConversationType.objects.all()
    


    def serialized_conversation_list(self):
        """
        Serialize the list of conversations related to the contact.
        """
        conversation_list = Conversation.objects.filter(user_id=self.request.user, 
                                                            contact_id = self.get_queryset()).order_by('-created_at')
        # Serialize the conversation list with pre-signed URLs using the ConversationViewSerializer
        serializer = ConversationViewSerializer(conversation_list, many=True)

        # Access the serialized data as a list using serializer.data
        serialized_conversation_list = serializer.data
        
        return serialized_conversation_list

    def get(self, request, *args, **kwargs):
        """
        Handles GET request for the conversation view.
        If a conversation_id is provided in the URL kwargs, it means we are viewing/editing an existing conversation.
        """
        conversation_id = self.kwargs.get('conversation_id')
        instance = self.get_queryset()
        conversation_data = {}
        if instance:
            if conversation_id:
                conversation_data = self.get_conversation_queryset().filter(contact_id = instance, pk=conversation_id).first() 
                serializer = self.serializer_class(instance=conversation_data)
            else:
                serializer = self.serializer_class()
            
            context= {'conversation_list':self.serialized_conversation_list(),
                                                        'serializer':serializer,
                                                        'contact_data':instance,
                                                        'is_edit': True if instance else False,
                                                        'conversation_data':conversation_data}
            return render_html_response(context,self.template_name)
        else:
            messages.error(request, " You are not authorized to perform this action.")
        return redirect(reverse('contact_list'))


    def post(self, request, *args, **kwargs):
        """
        Handles POST request for the conversation view.
        If contact_id is provided in URL kwargs, it means we are adding/updating a conversation related to the contact.
        """
        if kwargs.get('contact_id'):
            contact_data = self.get_queryset()
            if contact_data:
                conversation_id = self.kwargs.get('conversation_id')
                if conversation_id:
                    conversation_data = self.get_conversation_queryset().filter(contact_id = contact_data, pk=conversation_id).first() 
                    serializer = self.serializer_class(data=request.data,instance=conversation_data)
                    success = "Your conversation has been updated successfully."
                else:
                    serializer = self.serializer_class(data=request.data)
                    success = "Your conversation has been added successfully."
                
                if serializer.is_valid():
                    serializer.validated_data['user_id'] = request.user  # Assign the current user instance
                    serializer.validated_data['contact_id'] = contact_data # Assign the current user instance
                    serializer.save()
                    
                    if request.accepted_renderer.format == 'html':
                        messages.success(request, success)
                        return redirect(reverse('contact_conversation', kwargs={'contact_id': kwargs['contact_id']}))
                else:
                    # Invalid serializer data
                    if request.accepted_renderer.format == 'html':
                        # Render the HTML template with invalid serializer data
                        return render(request, self.template_name,{'conversation_list':self.serialized_conversation_list(),
                                                           'serializer':serializer,
                                                           'contact_data':contact_data})
                    else:   
                        # Return JSON response with error message
                        return create_api_response(status_code=status.HTTP_400_BAD_REQUEST,
                                            message="We apologize for the inconvenience, but please review the below information.",
                                            data=convert_serializer_errors(serializer.errors))
            else:
                messages.error(request, " You are not authorized to perform this action.")
        else:
            messages.error(request, " You are not authorized to perform this action.")
        return redirect(reverse('contact_list'))

class ConversationRemoveDocumentView(generics.DestroyAPIView):
    """
    View to remove a document associated with a conversation.
    """
    swagger_schema = None
    
    def get_queryset(self):
        """
        Get the queryset of contacts filtered by the current user.
        """
        user_id = self.request.user.id
        return Contact.objects.filter(pk=self.kwargs.get('contact_id')).get()
    
    def destroy(self, request, *args, **kwargs):
        """
        Handles DELETE request to remove the document associated with a conversation.
        """
        contact_data = self.get_queryset()
        conversation_id = kwargs.get('conversation_id')
        if conversation_id:
            conversation_instance = Conversation.objects.filter(contact_id=contact_data, pk=conversation_id).get()
            if conversation_instance and conversation_instance.document_path: 
                
                s3_client.delete_object(Bucket=settings.AWS_BUCKET_NAME, Key = conversation_instance.document_path)
                # Remove the document_path from the conversation instance and save
                conversation_instance.document_path = ''
                conversation_instance.save()
            return Response(
                {"message": "Your conversation has been deleted successfully."},
                status=status.HTTP_204_NO_CONTENT
            )
        else:
            return Response(
                {"message": "Conversation not found or you don't have permission to delete."},
                status=status.HTTP_404_NOT_FOUND
            )

class ConversationCommentView(generics.DestroyAPIView):
    """
    View to delete a conversation/comment.
    """
    swagger_schema = None
    
    def get_queryset(self):
        """
        Get the queryset of contacts filtered by the current user.
        """
        return Contact.objects.filter(pk=self.kwargs.get('contact_id')).get()
    
    def destroy(self, request, *args, **kwargs):
        """
        Handles DELETE request to delete a conversation/comment.
        """
        contact_data = self.get_queryset()
        conversation_id = kwargs.get('conversation_id')
        if conversation_id:
            conversation = Conversation.objects.filter(contact_id=contact_data, pk=conversation_id)
            conversation.delete()
            messages.success(request, "Your Conversation has been deleted successfully!")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="Your Conversation has been deleted successfully!", )
        else:
            messages.error(request, "Conversation not found OR You are not authorized to perform this action. ")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="Conversation not found OR You are not authorized to perform this action. ", )

class ExportCSVView(View):
    def get(self, request, *args, **kwargs):
        selected_ids_str = request.GET.get('stw_ids', '')
        if not selected_ids_str:
            messages.error(request, 'No Row was selected to export the data, Please selecte a row and try again.')
            return redirect('contact_list')

        selected_ids = selected_ids_str.split(',') if selected_ids_str else []

        # Fetch the selected data from the database
        selected_data = Contact.objects.filter(id__in=selected_ids).values(
            'first_name', 'last_name', 'email', 'phone_number','mobile_number','contact_type', 'job_title',
            'company_name','address','country','town','county','post_code'
        )

        # Create a CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="exported_data.csv"'

        # Create a CSV writer and write the header
        writer = csv.writer(response)
        header_row = [
            'First Name', 'Last Name', 'Email', 'Phone Number', 'Mobile Number', 'Contact Type', 'Job Title',
            'Company Name', 'Address', 'Country', 'Town', 'County', 'Post Code'
        ]
        writer.writerow([smart_str(header) for header in header_row])
       

        # Write data rows
        for data_row in selected_data:
            writer.writerow([
                data_row['first_name'],
                data_row['last_name'],
                data_row['email'],
                data_row['phone_number'], 
                data_row['mobile_number'], 
                data_row['contact_type'],
                data_row['job_title'],
                data_row['company_name'], 
                data_row['address'], 
                data_row['country'],
                data_row['town'],
                data_row['county'],
                data_row['post_code']
            ])

        return response
