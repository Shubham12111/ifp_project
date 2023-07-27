
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

    def get_queryset(self):
        """
        Get the filtered queryset for contacts based on the authenticated user.
        """
        queryset = Contact.objects.filter(user_id=self.request.user.id).order_by('-created_at')
        return queryset
    
    def get(self, request, *args, **kwargs):
        """
        Handle both AJAX (JSON) and HTML requests.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user = self.handle_unauthenticated()

        if isinstance(authenticated_user, HttpResponseRedirect):
            # If the user is not authenticated and a redirect response is received
            # (for HTML renderer), return the redirect response as it is.
            return authenticated_user
        
        if not authenticated_user:
            raise AuthenticationFailed("Authentication credentials were not provided")
        else:
            queryset = self.get_queryset()
            
            if request.accepted_renderer.format == 'html':
                context = {'contacts':queryset}
                return render_html_response(context,self.template_name)
            else:
                serializer = self.serializer_class(queryset, many=True)
                return create_api_response(status_code=status.HTTP_200_OK,
                                                message="Data retrieved",
                                                data=serializer.data)

class ContactAddUpdateView(CustomAuthenticationMixin, generics.CreateAPIView):
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
        authenticated_user = self.handle_unauthenticated()

        if isinstance(authenticated_user, HttpResponseRedirect):
            # If the user is not authenticated and a redirect response is received
            # (for HTML renderer), return the redirect response as it is.
            return authenticated_user
        
        if not authenticated_user:
            raise AuthenticationFailed("Authentication credentials were not provided")
        
        else:
            if kwargs.get('pk'):  # If a primary key is provided, it means we are editing an existing contact
                contact = self.get_queryset()
                serializer = self.serializer_class(instance=contact)
                context = {'serializer':serializer, 'contact':contact}
                return render_html_response(context,self.template_name)
            else:
                return create_api_response(status_code=status.HTTP_201_CREATED,
                                       message="GET Method Not Alloweded",)
        
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to add or update a contact.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user = self.handle_unauthenticated()

        if isinstance(authenticated_user, HttpResponseRedirect):
            # If the user is not authenticated and a redirect response is received
            # (for HTML renderer), return the redirect response as it is.
            return authenticated_user
        
        if not authenticated_user:
            raise AuthenticationFailed("Authentication credentials were not provided")
        
        else:
            if kwargs.get('pk'):
                # If a primary key is provided, it means we are editing an existing contact
                contact = self.get_queryset()
                message = "Congratulations! your contact has been updated successfully."
                serializer = self.serializer_class(contact, data=request.data)
            else:
                # If no primary key is provided, it means we are adding a new contact
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
                                        message="Congratulations! your contact has been added/updated successfully.",
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
        authenticated_user = self.handle_unauthenticated()

        if isinstance(authenticated_user, HttpResponseRedirect):
            # If the user is not authenticated and a redirect response is received
            # (for HTML renderer), return the redirect response as it is.
            return authenticated_user
        
        if not authenticated_user:
            raise AuthenticationFailed("Authentication credentials were not provided")
        
        contact = Contact.objects.filter(pk=self.kwargs.get('pk'),user_id=self.request.user.id).first()
        if contact:
            # Proceed with the deletion
            contact.delete()
        
            if request.accepted_renderer.format == 'html':
                messages.success(request, "Your contact has been deleted successfully!")
                return HttpResponse(status=204)  # HTTP 204 No Content (optional, can be any status code)
            else:
                # If the request is from API renderer, return a JSON response
                return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="Your contact has been deleted successfully!", )
        else:
            if request.accepted_renderer.format == 'html':
                messages.error(request, "Contact not found")
                return HttpResponse(status=404)  # HTTP 404 Not Found (optional, can be any status code)
            else:
                return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="Contact not found", )
               

      
      
class ConversationView(APIView):
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
        return Contact.objects.filter(user_id=self.request.user)

    def get_conversation_queryset(self):
        """
        Get the queryset of conversations filtered by the current user.
        """
        return Conversation.objects.filter(user_id=self.request.user)
    
    def get_object(self):
        """
        Get the contact instance based on the 'contact_id' from the URL kwargs.
        """
        contact_id = self.kwargs.get('contact_id')
        return self.get_queryset().filter(pk=contact_id).first()

    def serialized_conversation_list(self):
        """
        Serialize the list of conversations related to the contact.
        """
        conversation_list = Conversation.objects.filter(user_id=self.request.user, 
                                                            contact_id = self.get_object()).order_by('-created_at')
        # Serialize the conversation list with pre-signed URLs using the ConversationViewSerializer
        serializer = ConversationViewSerializer(conversation_list, many=True)

        # Access the serialized data as a list using serializer.data
        serialized_conversation_list = serializer.data
        
        return serialized_conversation_list

    def render_html_response(self, serializer):
        """
        Render HTML response using the provided serializer and template name.
        """
        return Response({'serializer': serializer}, template_name=self.template_name)

    def get(self, request, *args, **kwargs):
        """
        Handles GET request for the conversation view.
        If a conversation_id is provided in the URL kwargs, it means we are viewing/editing an existing conversation.
        """
        instance = self.get_object()
        conversation_id = self.kwargs.get('conversation_id')
        if instance:
            if conversation_id:
                conversation_data = self.get_conversation_queryset().filter(contact_id = instance, pk=conversation_id).first() 
                serializer = self.serializer_class(instance=conversation_data)
            else:
                serializer = self.serializer_class()
            
            return render(request, self.template_name,{'conversation_list':self.serialized_conversation_list(),
                                                        'serializer':serializer,
                                                        'contact_data':instance})
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