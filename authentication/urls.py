from django.urls import path
from .views import LoginView, SignupView, ForgotPasswordView, VerifyOTPView


urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('forgot_password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('verify/', VerifyOTPView.as_view(), name='verify_otp'),
   
]
