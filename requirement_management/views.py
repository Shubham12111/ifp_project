from django.shortcuts import render, redirect
from infinity_fire_solutions.aws_helper import *
from infinity_fire_solutions.permission import *
from infinity_fire_solutions.response_schemas import create_api_response, convert_serializer_errors, render_html_response
from rest_framework import generics, status
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from .serializers import RequirementSerializer, RequirementAddSerializer, RequirementDefectAddSerializer, RequirementDetailSerializer
from .models import Requirement, RequirementDefect
from django.contrib import messages
from rest_framework.response import Response
from rest_framework import filters


class RequirementListView(CustomAuthenticationMixin,generics.ListAPIView):
    """
    View to get the listing of all requirements.
    Supports both HTML and JSON response formats.
    """
    serializer_class = RequirementSerializer
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    filter_backends = [filters.SearchFilter]
    search_fields = ['customer_id__first_name', 'customer_id__last_name']
    template_name = 'requirement_list.html'
    ordering_fields = ['created_at'] 

    def get(self, request, *args, **kwargs):
        """
        Handle both AJAX (JSON) and HTML requests.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access.
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self,"requirement", HasListDataPermission, 'list'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        # Define a mapping of data access values to corresponding filters.
        filter_mapping = {
            "self": Q(customer_id=request.user ),
            "all": Q(),  # An empty Q() object returns all data.
        }
        # Get the appropriate filter from the mapping based on the data access value,
        # or use an empty Q() object if the value is not in the mapping.
        queryset = Requirement.objects.filter(filter_mapping.get(data_access_value, Q())).distinct().order_by('-created_at')
       
        if request.accepted_renderer.format == 'html':
            context = {'requirements':queryset}
            return render_html_response(context,self.template_name)
        else:
            serializer = self.serializer_class(queryset, many=True)
            return create_api_response(status_code=status.HTTP_200_OK,
                                            message="Data retrieved",
                                            data=serializer.data)


class RequirementAddView(CustomAuthenticationMixin, generics.CreateAPIView):
    """
    View for adding  a requirement.
    Supports both HTML and JSON response formats.
    """
    serializer_class = RequirementAddSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'requirement.html'
    
    # def get_queryset(self):
    #     """
    #     Get the filtered queryset for requirements based on the authenticated user.
    #     """
    #     queryset = Requirement.objects.filter(pk=self.kwargs.get('pk'),user_id=self.request.user.id).order_by('-created_at').first()
    #     return queryset
    
    def get(self, request, *args, **kwargs):
        """
        Handle GET request to display a form for adding a requirement.
        If the requirement exists, retrieve the serialized data and render the HTML template.
        If the requirement does not exist, render the HTML template with an empty serializer.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"requirement", HasCreateDataPermission, 'add'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        if request.accepted_renderer.format == 'html':
            context = {'serializer':self.serializer_class()}
            return render_html_response(context,self.template_name)
        else:
            return create_api_response(status_code=status.HTTP_201_CREATED,
                                message="GET Method Not Alloweded",)
        
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to add a requirement.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access.
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"requirement", HasCreateDataPermission, 'add'
        )
        message = "Congratulations! your requirement has been added successfully."
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            serializer.validated_data['user_id'] = request.user  # Assign the current user instance.
            serializer.save()

            if request.accepted_renderer.format == 'html':
                messages.success(request, message)
                return redirect(reverse('requirement_list'))

            else:
                # Return JSON response with success message and serialized data.
                return create_api_response(status_code=status.HTTP_201_CREATED,
                                    message=message,
                                    data=serializer.data
                                    )
        else:
            # Invalid serializer data.
            if request.accepted_renderer.format == 'html':
                # Render the HTML template with invalid serializer data.
                context = {'serializer':serializer}
                return render_html_response(context,self.template_name)
            else:   
                # Return JSON response with error message.
                return create_api_response(status_code=status.HTTP_400_BAD_REQUEST,
                                    message="We apologize for the inconvenience, but please review the below information.",
                                    data=convert_serializer_errors(serializer.errors))
            

class RequirementUpdateView(CustomAuthenticationMixin, generics.UpdateAPIView):
    """
    API view for updating a requirement.

    This view handles both HTML and API requests for updating a requirement instance.
    If the requirement instance exists, it will be updated with the provided data.
    Otherwise, an error message will be returned.

    The following request methods are supported:
    - POST: Updates the requirement instance.

    Note: Make sure to replace 'your_template_name.html' with the appropriate HTML template name.
    """
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'requirement.html'
    serializer_class = RequirementAddSerializer
    
    def get_queryset(self):
        """
        Get the queryset for listing Requirement items.

        Returns:
            QuerySet: A queryset of Requirements items filtered based on the authenticated user's ID.
        """
        # Get the model class using the provided module_name string
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "requirement", HasUpdateDataPermission, 'change'
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
        queryset = Requirement.objects.filter(filter_mapping.get(data_access_value, Q())).distinct().order_by('-created_at')
        queryset = queryset.filter(pk=self.kwargs.get('pk')).first()
        
        return queryset
    
    def get(self, request, *args, **kwargs):
        # This method handles GET requests for updating an existing Requirement object.
        if request.accepted_renderer.format == 'html':
            instance = self.get_queryset()
            if instance:
                serializer = self.serializer_class(instance=instance, context={'request': request})
                context = {'serializer': serializer, 'instance': instance}
                return render_html_response(context, self.template_name)
            else:
                messages.error(request, "You are not authorized to perform this action")
                return redirect(reverse('requirement_list'))
    
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to update a requirement instance.

        Args:
            request (rest_framework.request.Request): The HTTP request object.
            *args: Variable-length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            rest_framework.response.Response: HTTP response object.
                If successful, the requirement is updated, and the appropriate response is returned.
                If unsuccessful, an error response is returned.
        """
        data = request.data
        instance = self.get_queryset()
        if instance:
            # If the requirement instance exists, initialize the serializer with instance and provided data.
            serializer = self.serializer_class(instance=instance, data=data, context={'request': request})

            if serializer.is_valid():
                # If the serializer data is valid, save the updated requirement instance.
                serializer.save()
                message = "Your requirement has been updated successfully!"

                if request.accepted_renderer.format == 'html':
                    # For HTML requests, display a success message and redirect to requirement_list.
                    messages.success(request, message)
                    return redirect('requirement_list')
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
                # For HTML requests with no instance, display an error message and redirect to requirement_list.
                messages.error(request, error_message)
                return redirect('requirement_list')
            else:
                # For API requests with no instance, return an error response with an error message.
                return Response({'message': error_message}, status=status.HTTP_400_BAD_REQUEST)
            

class RequirementDeleteView(CustomAuthenticationMixin, generics.DestroyAPIView):
    """
    View for deleting a requirement.
    Supports both HTML and JSON response formats.
    """
    serializer_class = RequirementSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    # permission_classes = [IsAuthenticated]
    template_name = 'requirement.html'
    
    def delete(self, request, *args, **kwargs):
        """
        Handle DELETE request to delete a requirement.
        """
        # Get the requirement instance from the database.
         # Call the handle_unauthenticated method to handle unauthenticated access.
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self,"requirement", HasDeleteDataPermission, 'delete'
        )
        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(user_id=request.user ),
            "all": Q(),  # An empty Q() object returns all data
        }

        # Get the appropriate filter from the mapping based on the data access value,
        # or use an empty Q() object if the value is not in the mapping
        queryset = Requirement.objects.filter(filter_mapping.get(data_access_value, Q()))
        instance = queryset.filter(pk=self.kwargs.get('pk')).first()
        requirement = Requirement.objects.filter(pk=self.kwargs.get('pk'),user_id=self.request.user.id).first()
        if requirement:
            # Proceed with the deletion
            requirement.delete()
            messages.success(request, "Your requirement has been deleted successfully!")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="Your requirement has been deleted successfully!", )
        else:
            messages.error(request, "Requirement not found")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="Requirement not found", )
        

class RequirementDetailView(CustomAuthenticationMixin, generics.RetrieveAPIView):
    """
    API view for updating a requirement.

    This view handles both HTML and API requests for updating a requirement instance.
    If the requirement instance exists, it will be updated with the provided data.
    Otherwise, an error message will be returned.

    The following request methods are supported:
    - POST: Updates the requirement instance.

    Note: Make sure to replace 'your_template_name.html' with the appropriate HTML template name.
    """
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'requirement_defect.html'
    serializer_class = RequirementDetailSerializer
    
    def get_queryset(self):
        """
        Get the queryset for listing Requirement items.

        Returns:
            QuerySet: A queryset of Requirements items filtered based on the authenticated user's ID.
        """
        # Get the model class using the provided module_name string
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "requirement", HasViewDataPermission, 'view'
        )
        
        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(user_id=self.request.user ),
            "all": Q(),  # An empty Q() object returns all data
        }

        # Get the appropriate filter from the mapping based on the data access value,
        # or use an empty Q() object if the value is not in the mapping
        queryset = Requirement.objects.filter(filter_mapping.get(data_access_value, Q())).distinct().order_by('-created_at')
        queryset = queryset.filter(pk=self.kwargs.get('pk')).first()
        
        return queryset
    
    def get(self, request, *args, **kwargs):
        # This method handles GET requests for updating an existing Requirement object.

        if request.accepted_renderer.format == 'html':
            instance = self.get_queryset()
            if instance:
                serializer = self.serializer_class(instance=instance, context={'request': request})
                context = {
                    'serializer': RequirementDefectAddSerializer,
                    'requirement_serializer': serializer,
                    'instance': instance,
                    }
                return render_html_response(context, self.template_name)
            else:
                messages.error(request, "You are not authorized to perform this action")
                return redirect(reverse('requirement_list'))
    


class RequirementDefectAddView(CustomAuthenticationMixin, generics.CreateAPIView):
    """
    View for adding  a requirement.
    Supports both HTML and JSON response formats.
    """
    # serializer_class = RequirementDefectAddSerializer
    serializer_class = RequirementDefectAddSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'requirement_defect.html'
    
    def get_queryset(self):
        """
        Get the filtered queryset for requirements based on the authenticated user.
        """
        queryset = Requirement.objects.filter(pk=self.kwargs.get('pk'),user_id=self.request.user.id).order_by('-created_at').first()
        return queryset
    
    # def get(self, request, *args, **kwargs):
    #     """
    #     Handle GET request to display a form for adding a requirement.
    #     If the requirement exists, retrieve the serialized data and render the HTML template.
    #     If the requirement does not exist, render the HTML template with an empty serializer.
    #     """
    #     # Call the handle_unauthenticated method to handle unauthenticated access
    #     authenticated_user, data_access_value = check_authentication_and_permissions(
    #        self,"requirement", HasCreateDataPermission, 'detail'
    #     ) 
    #     requirement_id = kwargs["pk"]
    #     instance = self.get_queryset()
    #     # breakpoint() 
    #     if request.accepted_renderer.format == 'html':
    #         # context = {'serializer':self.serializer_class()}
    #         # return render_html_response(context,self.template_name)
    #         # instance = self.get_queryset()
    #         if instance:
    #             requirement_serializer = RequirementDetailSerializer(instance=instance, context={'request': request})
    #             # breakpoint()
    #             context = {
    #                 'serializer': self.serializer_class(),
    #                 'requirement_serializer': requirement_serializer, 
    #                 'instance': instance
    #                 }
    #             return render_html_response(context, self.template_name)
    #         else:
    #             messages.error(request, "You are not authorized to perform this action")
    #             return redirect(reverse('requirement_list'))
    #     else:
    #         return create_api_response(status_code=status.HTTP_201_CREATED,
    #                             message="GET Method Not Alloweded",)
        
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to add a requirement.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access.
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"Requirement", HasCreateDataPermission, 'detail'
        )
        message = "Congratulations! your requirement has been added successfully."
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            # serializer.validated_data['user_id'] = request.user  # Assign the current user instance.
            serializer.save()

            if request.accepted_renderer.format == 'html':
                messages.success(request, message)
                return redirect(reverse('requirement_detail', kwargs={'pk': self.kwargs.get('pk')}))

            else:
                # Return JSON response with success message and serialized data.
                return create_api_response(status_code=status.HTTP_201_CREATED,
                                    message=message,
                                    data=serializer.data
                                    )
        else:
            # Invalid serializer data.
            if request.accepted_renderer.format == 'html':
                # Render the HTML template with invalid serializer data.
                context = {'serializer':serializer}
                return render_html_response(context,self.template_name)
            else:   
                # Return JSON response with error message.
                return create_api_response(status_code=status.HTTP_400_BAD_REQUEST,
                                    message="We apologize for the inconvenience, but please review the below information.",
                                    data=convert_serializer_errors(serializer.errors))
            


class RequirementDefectUpdateView(CustomAuthenticationMixin, generics.UpdateAPIView):
    """
    View for adding  a requirement.
    Supports both HTML and JSON response formats.
    """
    # serializer_class = RequirementDefectAddSerializer
    serializer_class = RequirementDefectAddSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'requirement_defect.html'
    
    def get_queryset(self):
        """
        Get the filtered queryset for requirements based on the authenticated user.
        """
        queryset = Requirement.objects.filter(pk=self.kwargs.get('pk'),user_id=self.request.user.id).order_by('-created_at').first()
        return queryset
    
    def get(self, request, *args, **kwargs):
        """
        Handle GET request to display a form for adding a requirement.
        If the requirement exists, retrieve the serialized data and render the HTML template.
        If the requirement does not exist, render the HTML template with an empty serializer.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"Requirement", HasCreateDataPermission, 'change'
        ) 
        requirement_id = kwargs["pk"]
        instance = self.get_queryset()
        if request.accepted_renderer.format == 'html':
            # context = {'serializer':self.serializer_class()}
            # return render_html_response(context,self.template_name)
            # instance = self.get_queryset()
            if instance:
                requirement_serializer = RequirementDetailSerializer(instance=instance, context={'request': request})
                # breakpoint()
                context = {
                    'serializer': self.serializer_class(),
                    'requirement_serializer': requirement_serializer, 
                    'instance': instance
                    }
                return render_html_response(context, self.template_name)
            else:
                messages.error(request, "You are not authorized to perform this action")
                return redirect(reverse('requirement_list'))
        else:
            return create_api_response(status_code=status.HTTP_201_CREATED,
                                message="GET Method Not Alloweded",)
        
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to add a requirement.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access.
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"Requirement", HasCreateDataPermission, 'detail'
        )
        message = "Congratulations! your requirement has been added successfully."
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            # serializer.validated_data['user_id'] = request.user  # Assign the current user instance.
            serializer.save()

            if request.accepted_renderer.format == 'html':
                messages.success(request, message)
                return redirect(reverse('requirement_detail', kwargs={'pk': self.kwargs.get('pk')}))

            else:
                # Return JSON response with success message and serialized data.
                return create_api_response(status_code=status.HTTP_201_CREATED,
                                    message=message,
                                    data=serializer.data
                                    )
        else:
            # Invalid serializer data.
            if request.accepted_renderer.format == 'html':
                # Render the HTML template with invalid serializer data.
                context = {'serializer':serializer}
                return render_html_response(context,self.template_name)
            else:   
                # Return JSON response with error message.
                return create_api_response(status_code=status.HTTP_400_BAD_REQUEST,
                                    message="We apologize for the inconvenience, but please review the below information.",
                                    data=convert_serializer_errors(serializer.errors))