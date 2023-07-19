
# views.py
from django.shortcuts import render
from django.views import View
from .models import *
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer,JSONRenderer
from django.contrib import messages
from .models import Contact
from .serializers import ContactSerializer

class ContactListCreateView(generics.ListCreateAPIView):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    template_name = 'contact_list.html'

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            messages.success(request, 'Contact added successfully.')
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            for field, errors in serializer.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if request.accepted_renderer.format == 'html':
            # If the client accepts HTML, render the template
            return Response({'contacts': queryset}, template_name=self.template_name)
        # If the client accepts JSON, serialize the data and return it
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)  # Pass the contacts queryset to the template
      
      
class MessageListView(View):
    template_name = 'messages.html'

    def get(self, request):
        messages = Contact.objects.all()
        return render(request, self.template_name, {'messages': messages})

