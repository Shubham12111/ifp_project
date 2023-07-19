from django.urls import path
from .views import LoginView, SignupView, ForgotPasswordView, VerifyOTPView,LogoutView, ProfileView, ChangePasswordView


urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('forgot_password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('verify/', VerifyOTPView.as_view(), name='verify_otp'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('change_password/', ChangePasswordView.as_view(), name='change_password'),
   
]
