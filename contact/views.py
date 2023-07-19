from django.contrib import messages
from django.views import View
from django.urls import reverse
from django.shortcuts import render,redirect
from django.http import Http404

from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.renderers import TemplateHTMLRenderer,JSONRenderer
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer
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


    def get(self, request, *args, **kwargs):
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

    
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            
            if request.accepted_renderer.format == 'html':
                # Render the HTML template with invalid serializer data
                messages.success(request, "Congratulations! your contact has been added successfully.")
                return redirect(reverse('list'))

            else:
                # Return JSON response with success message and serialized data
                return create_api_response(status_code=status.HTTP_201_CREATED,
                                       message="Congratulations! your contact has been added successfully.",
                                       data=serializer.data
                                        )
        else:
            # Invalid serializer data
            if request.accepted_renderer.format == 'html':
                # Render the HTML template with invalid serializer data
                context = {'serializer': serializer, 'errors': convert_serializer_errors(serializer.errors)}
                return self.render_html_response(context)
            else:
                # Return JSON response with error message
                return create_api_response(status_code=status.HTTP_400_BAD_REQUEST,
                                           message="We apologize for the inconvenience, but please review the below information.",
                                           data=convert_serializer_errors(serializer.errors))
            
    def put(self, request, *args, **kwargs):
        instance = self.get_object(kwargs['pk'])
        serializer = self.serializer_class(instance, data=request.data)
        if serializer.is_valid():
            serializer.save()

            if request.accepted_renderer.format == 'html':
                # Render the HTML template with invalid serializer data
                messages.success(request, "Great! your contact has been updated successfully")
                return redirect(reverse('list'))
            
            return create_api_response(status_code=status.HTTP_200_OK,
                                       message="Great! your contact has been updated successfully.",
                                       data=serializer.data
                                       )
        else:
            if request.accepted_renderer.format == 'html':
                # Render the HTML template with invalid serializer data
                context = {'serializer': serializer, 'errors': convert_serializer_errors(serializer.errors)}
                return self.render_html_response(context)
            else:
                # Return JSON response with error message
                return create_api_response(status_code=status.HTTP_400_BAD_REQUEST,
                                           message="We apologize for the inconvenience, but please review the below information.",
                                           data=convert_serializer_errors(serializer.errors))
            

        





# class ContactRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
#     queryset = Contact.objects.all()
#     serializer_class = ContactSerializer
#     renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
#     renderer_classes = [TemplateHTMLRenderer,]
#     template_name = 'contact_list.html'

#     def render_to_response(self, context, **response_kwargs):
#         return Response(context, template_name=self.template_name)

#     def get(self, request, *args, **kwargs):
#         instance = self.get_object()
#         serializer = self.serializer_class(instance)
#         return self.render_to_response({'serializer': serializer, 'action': 'Edit'})

#     def put(self, request, *args, **kwargs):
#         instance = self.get_object()
#         serializer = self.serializer_class(instance, data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return create_api_response(status_code=status.HTTP_200_OK,
#                                        message="Please ensure that the entered details are correct and try again.",
#                                        data=serializer.data
#                                        )
#         else:
#             return self.render_to_response({'serializer': serializer, 'action': 'Edit'})

#     def delete(self, request, *args, **kwargs):
#         instance = self.get_object()
#         instance.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)

    
    

