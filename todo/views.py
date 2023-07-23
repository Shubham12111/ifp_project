from django.http import JsonResponse
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer,JSONRenderer
from infinity_fire_solutions.response_schemas import create_api_response, render_html_response
from .models import *
from .serializers import *
from django.contrib import messages 
from django.shortcuts import redirect
from django.urls import reverse
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied

class GroupAndMethodBasedPermission(BasePermission):
    def __init__(self, model_name, method_name, allowed_methods):
        self.model_name = model_name
        self.method_name = method_name
        self.allowed_methods = allowed_methods

    def has_permission(self, request, view):
        # Check if the user belongs to any of the allowed groups
        required_permission = f"{self.method_name}_{self.model_name.lower()}"
        user_groups = request.user.groups.all()
        for group in user_groups:
            for permission in group.permissions.all():
                if permission.codename == required_permission:
                    return request.method in self.allowed_methods
        
        # Raise a PermissionDenied exception with an error message
        raise PermissionDenied("You don't have permission to perform this action.")

class ToDoView(APIView):
    """ View to get the listing of all contacts """
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'todo_list.html'
    
    
    def get_queryset(self):
        queryset = Todo.objects.all()
        user_id = self.request.user.id
        return queryset.filter(user_id=user_id)

    def get_permissions(self):
        if self.request.method == 'GET':
            return [GroupAndMethodBasedPermission(model_name='Todo', method_name='view', allowed_methods=['GET'])]
        elif self.request.method == 'POST':
            return [GroupAndMethodBasedPermission(model_name='Todo', method_name='add', allowed_methods=['POST'])]
        else:
            return super().get_permissions()


    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        if request.accepted_renderer.format == 'html':
            # If the client accepts HTML, render the template
            context = {'todo_list': queryset}
            return render_html_response(context,self.template_name)
        else:
            serializer = self.serializer_class(queryset, many=True)
            return create_api_response(status_code=status.HTTP_200_OK,
                                       message="Data Retrieved successfully",
                                       data=serializer)
       


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

