from django.shortcuts import render

# Create your views here.
from django.shortcuts import render

def dashboard(request):
    # Add logic to fetch and process data for the dashboard if needed
    return render(request, 'dashboard.html')
