from rest_framework import serializers
from .models import Interview, ChatMessage


class InterviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interview
        fields = [
            'id',
            'job_title',
            'job_description',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = [
            'id',
            'role',
            'content',
            'created_at',
        ]
        read_only_fields = ['id', 'role', 'created_at']


class SendMessageSerializer(serializers.Serializer):
    """Validates incoming user message — not a ModelSerializer."""
    message = serializers.CharField(required=True, allow_blank=False)