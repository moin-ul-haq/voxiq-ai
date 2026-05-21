import hmac
import hashlib
from datetime import datetime, timezone

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.conf import settings

from interviews.models import Interview
from .models import MockInterviewSession
from .serializers import MockInterviewSessionSerializer
from .utils import create_vapi_assistant, delete_vapi_assistant


class SessionStartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """
        Create VAPI assistant dynamically and return assistant_id to frontend.
        Frontend uses this assistant_id to start VAPI call directly.
        """
        interview = get_object_or_404(Interview, pk=pk, user=request.user)

        try:
            vapi_assistant = create_vapi_assistant(
                interview=interview,
                user=request.user,
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to initialize voice session: {str(e)}'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        assistant_id = vapi_assistant.get('id')

        # Save session to DB
        session = MockInterviewSession.objects.create(
            interview=interview,
            vapi_assistant_id=assistant_id,
            status='initiated',
        )

        return Response({
            'session_id': session.id,
            'vapi_assistant_id': assistant_id,
            'status': session.status,
        }, status=status.HTTP_200_OK)


class SessionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """List all mock sessions for a specific interview."""
        interview = get_object_or_404(Interview, pk=pk, user=request.user)
        sessions = interview.mock_sessions.all().order_by('-started_at')
        serializer = MockInterviewSessionSerializer(sessions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SessionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        """Get single session with full transcript."""
        session = get_object_or_404(
            MockInterviewSession,
            pk=session_id,
            interview__user=request.user,
        )
        serializer = MockInterviewSessionSerializer(session)
        return Response(serializer.data, status=status.HTTP_200_OK)


class VapiWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Receive events from VAPI.
        Handles: call started, call ended (with transcript).
        Secured via VAPI webhook secret header verification.
        """

        # Verify webhook secret
        if not self._verify_webhook(request):
            return Response(
                {'error': 'Unauthorized'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        payload = request.data
        event_type = payload.get('message', {}).get('type')

        if event_type == 'end-of-call-report':
            self._handle_call_ended(payload)

        elif event_type == 'status-update':
            self._handle_status_update(payload)

        return Response({'received': True}, status=status.HTTP_200_OK)

    def _verify_webhook(self, request) -> bool:
        """Verify request is genuinely from VAPI using secret header."""
        webhook_secret = getattr(settings, 'VAPI_WEBHOOK_SECRET', None)

        # If no secret set yet (dev mode), skip verification
        if not webhook_secret:
            return True

        vapi_signature = request.headers.get('x-vapi-secret')
        return vapi_signature == webhook_secret

    def _handle_call_ended(self, payload):
        """Save transcript and mark session as completed."""
        message = payload.get('message', {})
        call = message.get('call', {})
        call_id = call.get('id')
        assistant_id = call.get('assistantId')

        if not call_id:
            return

        try:
            session = MockInterviewSession.objects.get(vapi_call_id=call_id)
        except MockInterviewSession.DoesNotExist:
            # Try finding by assistant_id if call_id not yet saved
            if assistant_id:
                try:
                    session = MockInterviewSession.objects.get(
                        vapi_assistant_id=assistant_id,
                        status__in=['initiated', 'in_progress']
                    )
                except MockInterviewSession.DoesNotExist:
                    return
            else:
                return

        session.vapi_call_id = call_id
        session.status = 'completed'
        session.transcript = message.get('transcript')
        session.duration_seconds = int(message.get('durationSeconds', 0))
        session.ended_at = datetime.now(timezone.utc)

        # Generate LLM evaluation from transcript
        from .utils import generate_interview_evaluation
        if session.transcript:
            session.evaluation = generate_interview_evaluation(session)

        session.save()

        # Clean up VAPI assistant after call ends
        if session.vapi_assistant_id:
            delete_vapi_assistant(session.vapi_assistant_id)

    def _handle_status_update(self, payload):
        """Update session status when call becomes active."""
        message = payload.get('message', {})
        call = message.get('call', {})
        call_id = call.get('id')
        assistant_id = call.get('assistantId')
        call_status = message.get('status')

        if call_status != 'in-progress' or not assistant_id:
            return

        try:
            session = MockInterviewSession.objects.get(
                vapi_assistant_id=assistant_id,
                status='initiated'
            )
            session.vapi_call_id = call_id
            session.status = 'in_progress'
            session.save(update_fields=['vapi_call_id', 'status'])
        except MockInterviewSession.DoesNotExist:
            pass