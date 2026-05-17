from django.urls import path
from .views import (
    InterviewListCreateView,
    InterviewDetailView,
    ChatView,
)

urlpatterns = [
    path('', InterviewListCreateView.as_view(), name='interview-list-create'),
    path('<int:pk>/', InterviewDetailView.as_view(), name='interview-detail'),
    path('<int:pk>/chat/', ChatView.as_view(), name='interview-chat'),
]