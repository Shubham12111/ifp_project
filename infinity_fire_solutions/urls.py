"""
URL configuration for infinity_fire_solutions project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions



# swagger settings
schema_view = get_schema_view(
   openapi.Info(
      title="Infinity Fire solution APIs",
      default_version='v0.2.0',
      description="Welcome to the Infinity Fire Solution API Documentation, offering effortless integration with our platform. </br><b>Please note that certain modules currently do not have associated APIs.</b> </br>These modules include:</br></br>1. Contact </br> </br>2. Todo Comments </br></br>3. Customer Billing Address </br></br>4. Customer Site Address  </br></br>5. Customer Contact Person  </br></br>6. Requriment Defect",
   ),
   public=True,
   permission_classes=[permissions.AllowAny]
)

# admin Customization
admin.site.site_header = "Infinity Fire Solutions Admin"
admin.site.site_title = "Infinity Fire Solutions"
admin.site.index_title = "Infinity Fire Solutions Management"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('authentication.urls')),
    path('contact/',include('contact.urls')),
    path('task/',include('todo.urls')),
    path('',include('common_app.urls')),
    path('customer/',include('customer_management.urls')),
    path('stock/',include('stock_management.urls')),
    path('fra/',include('requirement_management.urls')),
    path('purchase_order/',include('purchase_order_management.urls')),
    path('work_planning/',include('work_planning_management.urls')),







    #swagger links for the api documentation
    path('api/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),



] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
