from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    ProfileView,
    ResumeUploadView,
    CompleteOnboardingView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/resume/', ResumeUploadView.as_view(), name='resume-upload'),
    path('onboarding/complete/', CompleteOnboardingView.as_view(), name='onboarding-complete'),
]