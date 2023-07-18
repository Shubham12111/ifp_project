from django.urls import path
from .views import LoginView, SignupView, ForgotPasswordView, VerifyOTPView

app_name = 'accounts'

urlpatterns = [
    path('login/', LoginView.as_view(), name='log_in'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('forgot_password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('verify/', VerifyOTPView.as_view(), name='verify_otp'),
   
]
