from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import Interview, ChatMessage
from .serializers import (
    InterviewSerializer,
    ChatMessageSerializer,
    SendMessageSerializer,
)
from .utils import get_groq_response


class InterviewListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        interviews = Interview.objects.filter(user=request.user).order_by('-created_at')
        serializer = InterviewSerializer(interviews, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = InterviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InterviewDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        return get_object_or_404(Interview, pk=pk, user=user)

    def get(self, request, pk):
        interview = self.get_object(pk, request.user)
        serializer = InterviewSerializer(interview)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        interview = self.get_object(pk, request.user)
        serializer = InterviewSerializer(interview, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        interview = self.get_object(pk, request.user)
        interview.delete()
        return Response(
            {'message': 'Interview deleted successfully.'},
            status=status.HTTP_204_NO_CONTENT
        )


class ChatView(APIView):
    permission_classes = [IsAuthenticated]

    def get_interview(self, pk, user):
        return get_object_or_404(Interview, pk=pk, user=user)

    def get(self, request, pk):
        """Return full chat history for this interview."""
        interview = self.get_interview(pk, request.user)
        messages = interview.messages.all()
        serializer = ChatMessageSerializer(messages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, pk):
        """Send a message and get AI response."""
        interview = self.get_interview(pk, request.user)

        # Validate incoming message
        serializer = SendMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_message = serializer.validated_data['message']

        # Save user message to DB
        ChatMessage.objects.create(
            interview=interview,
            role='user',
            content=user_message,
        )

        # Build chat history for Groq (all previous messages)
        history = list(
            interview.messages.values('role', 'content').order_by('created_at')
        )

        # Get Groq response
        try:
            ai_response = get_groq_response(
                interview=interview,
                user=request.user,
                chat_history=history,
            )
        except Exception as e:
            print(f"Groq error: {e}")
            return Response(
        {'error': str(e)},  # change this temporarily
        status=status.HTTP_503_SERVICE_UNAVAILABLE
    )

        # Save assistant response to DB
        assistant_message = ChatMessage.objects.create(
            interview=interview,
            role='assistant',
            content=ai_response,
        )

        return Response(
            ChatMessageSerializer(assistant_message).data,
            status=status.HTTP_200_OK
        )