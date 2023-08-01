
from django.contrib import messages
from django.urls import reverse
from django.shortcuts import render, redirect
from django.http import Http404, JsonResponse, HttpResponse
from django.conf import settings
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

class ContactListView(CustomAuthenticationMixin,generics.ListAPIView):
    """
    View to get the listing of all contacts.
    Supports both HTML and JSON response formats.
    """
    serializer_class = ContactSerializer
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'email','contact_type__name']
    template_name = 'contact_list.html'
    ordering_fields = ['created_at'] 

    def get(self, request, *args, **kwargs):
        """
        Handle both AJAX (JSON) and HTML requests.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self,"contact", HasListDataPermission, 'list'
        )
        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(user_id=request.user ),
            "all": Q(),  # An empty Q() object returns all data
        }
        # Get the appropriate filter from the mapping based on the data access value,
        # or use an empty Q() object if the value is not in the mapping
        queryset = Contact.objects.filter(filter_mapping.get(data_access_value, Q())).distinct().order_by('-created_at')
       
        if request.accepted_renderer.format == 'html':
            context = {'contacts':queryset}
            return render_html_response(context,self.template_name)
        else:
            serializer = self.serializer_class(queryset, many=True)
            return create_api_response(status_code=status.HTTP_200_OK,
                                            message="Data retrieved",
                                            data=serializer.data)

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
           
        if request.accepted_renderer.format == 'html':
            context = {'serializer':self.serializer_class()}
            return render_html_response(context,self.template_name)
        else:
            return create_api_response(status_code=status.HTTP_201_CREATED,
                                message="GET Method Not Alloweded",)
        
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to add or update a contact.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"contact", HasCreateDataPermission, 'add'
        )
        message = "Congratulations! your contact has been added successfully."
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            serializer.validated_data['user_id'] = request.user  # Assign the current user instance
            serializer.save()

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

    
    def get(self, request, *args, **kwargs):
        # This method handles GET requests for updating an existing Conatct object.
        if request.accepted_renderer.format == 'html':
            instance = self.get_queryset()
            if instance:
                serializer = self.serializer_class(instance=instance, context={'request': request})
                context = {'serializer': serializer, 'instance': instance}
                return render_html_response(context, self.template_name)
            else:
                messages.error(request, "You are not authorized to perform this action")
                return redirect(reverse('contact_list'))
    
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
            serializer = self.serializer_class(instance=instance, data=data, context={'request': request})

            if serializer.is_valid():
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
    
    def delete(self, request, *args, **kwargs):
        """
        Handle DELETE request to delete a contact.
        """
        # Get the contact instance from the database
         # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self,"contact", HasDeleteDataPermission, 'delete'
        )
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
            instance.delete()
            return create_api_response(
                status.HTTP_200_OK,
                "Your contact has been deleted successfully.",
            )
        else:
            return create_api_response(
                status.HTTP_404_NOT_FOUND,
                "Contact not found or you don't have permission to delete."
            )
    

      
      
class ConversationView(CustomAuthenticationMixin, generics.RetrieveAPIView):
    """
    View to display and manage conversations related to a contact.
    """
    serializer_class = ConversationSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'conversation.html'
    
    
    def get_queryset(self):
        """
        Get the queryset of contacts filtered by the current user.
        """
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self,"contact", HasViewDataPermission, 'view'
        )
        
        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(user_id=self.request.user ),
            "all": Q(),  # An empty Q() object returns all data
        }
        
        # Get the appropriate filter from the mapping based on the data access value,
        # or use an empty Q() object if the value is not in the mapping
        queryset = Contact.objects.filter(filter_mapping.get(data_access_value, Q())).order_by('-created_at')
        queryset = queryset.filter(pk=self.kwargs.get('contact_id')).first()
        
        return queryset
    

    def get_conversation_queryset(self):
        """
        Get the queryset of conversations filtered by the current user.
        """
        return Conversation.objects.filter(user_id=self.request.user)

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
        instance = self.get_queryset()
        conversation_id = self.kwargs.get('conversation_id')
        if instance:
            if conversation_id:
                conversation_data = self.get_conversation_queryset().filter(contact_id = instance, pk=conversation_id).first() 
                serializer = self.serializer_class(instance=conversation_data)
            else:
                serializer = self.serializer_class()
            
            context= {'conversation_list':self.serialized_conversation_list(),
                                                        'serializer':serializer,
                                                        'contact_data':instance}
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
            contact_data = Contact.objects.filter(user_id = request.user, 
                                                  pk = kwargs.get('contact_id')).first()
            if contact_data:
                conversation_id = self.kwargs.get('conversation_id')
                if conversation_id:
                    conversation_data = self.get_conversation_queryset().filter(contact_id = contact_data, pk=conversation_id).first() 
                    serializer = self.serializer_class(data=request.data,instance=conversation_data)
                    success = "Congratulations! your conversation has been updated successfully."
                else:
                    serializer = self.serializer_class(data=request.data)
                    success = "Congratulations! your conversation has been added successfully."
                
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
    
    def get_queryset(self):
        """
        Get the queryset of contacts filtered by the current user.
        """
        user_id = self.request.user.id
        return Contact.objects.filter(pk=self.kwargs.get('contact_id'), user_id=user_id).get()
    
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
    
    def get_queryset(self):
        """
        Get the queryset of contacts filtered by the current user.
        """
        user_id = self.request.user.id
        return Contact.objects.filter(pk=self.kwargs.get('contact_id'), user_id=user_id).get()
    
    def destroy(self, request, *args, **kwargs):
        """
        Handles DELETE request to delete a conversation/comment.
        """
        contact_data = self.get_queryset()
        conversation_id = kwargs.get('conversation_id')
        if conversation_id:
            conversation = Conversation.objects.filter(contact_id=contact_data, pk=conversation_id)
            conversation.delete()
            return Response(
                {"message": "Your conversation has been deleted successfully."},
                status=status.HTTP_204_NO_CONTENT
            )
        else:
            return Response(
                {"message": "Conversation not found or you don't have permission to delete."},
                status=status.HTTP_404_NOT_FOUND
            )