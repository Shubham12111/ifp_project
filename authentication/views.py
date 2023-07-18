from django.shortcuts import render

# Create your views here.
# views.py

from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from rest_framework.views import APIView
from rest_framework.renderers import TemplateHTMLRenderer, JSONOpenAPIRenderer

class LoginView(APIView):
    renderer_classes = [TemplateHTMLRenderer, JSONOpenAPIRenderer]
    template_name = 'login.html'

    def get(self, request):
        return 

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            # Redirect to a success page or return an API response
            return redirect('home')
        else:
            # Handle invalid credentials case
            return render(request, 'login.html', {'error': 'Invalid username or password'})

