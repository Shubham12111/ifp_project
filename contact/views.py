
from django.contrib import messages
from django.views import View
from django.urls import reverse
from django.shortcuts import render,redirect
from django.http import Http404
from django.http import JsonResponse, HttpResponse

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


from infinity_fire_solutions.response_schemas import create_api_response,convert_serializer_errors,render_html_response
from cities_light.models import City, Country, Region

from .models import Contact
from .serializers import ContactSerializer,ConversationSerializer


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
    
    
    def get_queryset(self):
        queryset = Contact.objects.filter(user_id=self.request.user.id).order_by('-created_at')
        return queryset
    
    def handle_html_request(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if request.accepted_renderer.format == 'html':
            # If the client accepts HTML, render the template
            context = {'contacts':queryset}
            return render_html_response(context,self.template_name)
        
       # If the client accepts JSON, serialize the data and return it
        serializer = self.serializer_class(queryset, many=True)

        return create_api_response(status_code=status.HTTP_200_OK,
                                    message="Data retrieved",
                                    data=serializer.data)

    

class ContactAddUpdateView(generics.CreateAPIView):
    serializer_class = ContactSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    # permission_classes = [IsAuthenticated]
    template_name = 'contact.html'

    
    def get_queryset(self):
        queryset = Contact.objects.filter(pk=self.kwargs.get('pk'),user_id=self.request.user.id).order_by('-created_at')
        return queryset

    def get(self, request, *args, **kwargs):
        if kwargs.get('pk'):  # If a primary key is provided, it means we are editing an existing contact
            contact = self.get_queryset().get()
            serializer = self.serializer_class(instance=contact)
            context = {'serializer':serializer, 'contact':contact}
            return render_html_response(context,self.template_name)
        else:
            serializer = self.serializer_class()
            context = {'serializer':serializer}
            return render_html_response(context, self.template_name)
    
    def post(self, request, *args, **kwargs):
        if kwargs.get('pk'):
            # If a primary key is provided, it means we are editing an existing contact
            contact = self.get_queryset().get()
            serializer = self.serializer_class(contact, data=request.data)
        else:
            # If no primary key is provided, it means we are adding a new contact
            serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            serializer.validated_data['user_id'] = request.user  # Assign the current user instance
            serializer.save()

            if request.accepted_renderer.format == 'html':
                # Render the HTML template with invalid serializer data
                if kwargs.get('pk'):
                    messages.success(request, "Congratulations! your contact has been updated successfully.")
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
                context = {'serializer':serializer}
                return render_html_response(context,self.template_name)
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
        if contact:

            # Proceed with the deletion
            contact.delete()
        
            if request.accepted_renderer.format == 'html':
                messages.success(request, "Your contact has been deleted successfully!")
                return HttpResponse(status=204)  # HTTP 204 No Content (optional, can be any status code)
            else:
                # If the request is from API renderer, return a JSON response
                return JsonResponse({"message": "Your contact has been deleted successfully!"})
        else:
            if request.accepted_renderer.format == 'html':
                messages.error(request, "Contact not found")
                return HttpResponse(status=404)  # HTTP 404 Not Found (optional, can be any status code)
            else:
                return JsonResponse({"message": "Contact not found"}, status=404)

      
      
class ConversationView(APIView):
    serializer_class = ConversationSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'conversation.html'
    
    
    def get_queryset(self):
        return Contact.objects.filter(user_id=self.request.user)

    def get_conversation_queryset(self):
        return Conversation.objects.filter(user_id=self.request.user)
    
    def get_object(self):
        contact_id = self.kwargs.get('contact_id')
        return self.get_queryset().filter(pk=contact_id).first()

    def render_html_response(self, serializer):
        """
        Render HTML response using the provided serializer and template name.
        """
        return Response({'serializer': serializer}, template_name=self.template_name)

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        conversation_id = self.kwargs.get('conversation_id')
        if instance:
            if conversation_id:
                conversation_data = self.get_conversation_queryset().filter(contact_id = instance, pk=conversation_id).first() 
                serializer = self.serializer_class(instance=conversation_data)
            else:
                serializer = self.serializer_class()
            conversation_list = Conversation.objects.filter(user_id=request.user, 
                                                            contact_id = instance).order_by('-created_at')
            
            return render(request, self.template_name,{'conversation_list':conversation_list,
                                                        'serializer':serializer,
                                                        'contact_data':instance})
        else:
            messages.error(request, " You are not authorized to perform this action.")
        return redirect(reverse('contact_list'))


    def post(self, request, *args, **kwargs):
        if kwargs.get('contact_id'):
            contact_data = Contact.objects.filter(user_id = request.user, 
                                                  pk = kwargs.get('contact_id')).first()
            if contact_data:
                conversation_id = self.kwargs.get('conversation_id')
                conversation_list = Conversation.objects.filter(user_id=request.user, 
                                                                contact_id = contact_data).order_by('-created_at')
                
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
                        return render(request, self.template_name,{'conversation_list':conversation_list,
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
    

class ConversationCommentView(generics.DestroyAPIView):
    
    def get_queryset(self):
        user_id = self.request.user.id
        return Contact.objects.filter(pk=self.kwargs.get('contact_id'), user_id=user_id).get()
    
    def destroy(self, request, *args, **kwargs):
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