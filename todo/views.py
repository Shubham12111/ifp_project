from django.http import JsonResponse
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer,JSONRenderer
from infinity_fire_solutions.response_schemas import create_api_response
from .models import *
from .serializers import *
from django.contrib import messages 
from django.shortcuts import redirect
from django.urls import reverse
from django.shortcuts import get_object_or_404

class ToDoListView(generics.ListAPIView):
    """ view to get the listing of all contacts
    """
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'todo_list.html'

    def get(self, request, *args, **kwargs):
        queryset = Todo.objects.filter(user_id=request.user)

        if request.accepted_renderer.format == 'html':
            # If the client accepts HTML, render the template
            return Response({'todo_list': queryset}, template_name=self.template_name)
        else:
            serializer = self.serializer_class(queryset, many=True)
            return create_api_response(status_code=status.HTTP_200_OK,
                                       message="Data Retrieved successfully",
                                       data=serializer)
        
        # # If the client accepts JSON (DataTable's request), handle server-side processing
        # draw = int(request.GET.get('draw', 1))
        # start = int(request.GET.get('start', 0))
        # length = int(request.GET.get('length', 10))
        # search_value = request.GET.get('search[value]', None)

        # if search_value:
        #     queryset = queryset.filter(title__icontains=search_value)

        # total_records = queryset.count()
        # queryset = queryset[start:start + length]

        # serializer = self.serializer_class(queryset, many=True)

        # print(queryset, queryset)
        # return JsonResponse({
        #     'draw': draw,
        #     'recordsTotal': total_records,
        #     'recordsFiltered': total_records,
        #     'data': serializer.data
        # })


class ToDoAddView(generics.CreateAPIView):
    
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'todo_add.html'
    serializer_class = TodoAddSerializer

    def render_html_response(self, serializer):
        """
        Render HTML response using the provided serializer and template name.
        """
        return Response({'serializer': serializer}, template_name=self.template_name)
    
        
    def get(self, request, *args, **kwargs):
        
        if kwargs.get('pk'):

            # If a primary key is provided, it means we are editing an existing contact
            data = get_object_or_404(Todo, pk=kwargs.get('pk'), user_id=request.user)
            serializer = self.serializer_class(instance=data)
        else:
            # If no primary key is provided, it means we are adding a new contact
            serializer = self.serializer_class()

        if request.accepted_renderer.format == 'html':
            # If the client accepts HTML, render the template
            return self.render_html_response(serializer)
    
    def post(self, request, *args, **kwargs):

        data = request.data

        if kwargs.get('pk'):
            # If a primary key is provided, it means we are editing an existing contact
            todo_data = get_object_or_404(Todo, pk=kwargs.get('pk'), user_id=request.user)
            serializer = self.serializer_class(instance=todo_data, data=data)
        else:
            # If no primary key is provided, it means we are adding a new contact
            serializer = self.serializer_class(data=data)

        

        serializer = self.serializer_class(data=data)

        if serializer.is_valid():
            serializer.validated_data['user_id'] = request.user 
            serializer.save()
            if request.accepted_renderer.format == 'html':
                messages.success(request, f"Task Added: Your TODO have been saved successfully! ")
                return redirect(reverse('todo_list'))
            else:
                return create_api_response(status_code=status.HTTP_200_OK,
                                           message="Data retrived succefully",
                                           data=serializer.data
                                           )
        else:
            # Render the HTML template with invalid serializer data
            return self.render_html_response(serializer)

