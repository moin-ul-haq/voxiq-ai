from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import authenticate, get_user_model


from .serializers import (
    RegisterSerializer,
    UserProfileSerializer,
    ResumeUploadSerializer,
    LoginResponseSerializer,
)
from .utils import extract_text_from_resume

User = get_user_model()


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                RegisterSerializer(user).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {'error': 'Email and password are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, username=email, password=password)

        if not user:
            return Response(
                {'error': 'Invalid credentials.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': LoginResponseSerializer(user).data,
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response(
                {'error': 'Refresh token is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {'message': 'Logged out successfully.'},
                status=status.HTTP_200_OK
            )
        except TokenError:
            return Response(
                {'error': 'Invalid or expired token.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = UserProfileSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResumeUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return a fresh presigned URL for the user's resume."""
        user = request.user
        if not user.resume:
            return Response(
                {'error': 'No resume uploaded.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Generate a fresh presigned URL from the storage backend
        resume_url = user.resume.url
        return Response({
            'resume_url': resume_url,
        }, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ResumeUploadSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            user = serializer.save()

            # Extract text from uploaded resume and save for AI context
            try:
                resume_text = extract_text_from_resume(user.resume)
                user.resume_text = resume_text
                user.save(update_fields=['resume_text'])
            except Exception:
                # Resume saved even if text extraction fails
                pass

            return Response({
                'message': 'Resume uploaded successfully.',
                'resume_url': user.resume.url,
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CompleteOnboardingView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        user = request.user
        user.onboarding_complete = True
        user.save(update_fields=['onboarding_complete'])
        return Response(
            {'message': 'Onboarding complete.'},
            status=status.HTTP_200_OK
        )


# ──────────────────────────────────────────────────────
# OAuth Views (REST API)
# ──────────────────────────────────────────────────────

from .oauth import (
    build_auth_url,
    exchange_code_for_token,
    get_user_info,
    get_or_create_oauth_user,
    validate_provider,
)

class OAuthAuthURLView(APIView):
    """
    GET /api/auth/oauth/<provider>/auth-url/?redirect_uri=...

    Returns the OAuth consent screen URL for the given provider.
    The frontend should provide the redirect_uri it will use for the callback.
    """
    permission_classes = [AllowAny]

    def get(self, request, provider):
        # Frontend must pass its callback URL (e.g. http://localhost:5173/auth/callback)
        redirect_uri = request.query_params.get('redirect_uri')
        if not redirect_uri:
            from django.conf import settings
            redirect_uri = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173') + '/auth/callback'

        try:
            auth_url = build_auth_url(provider, redirect_uri)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({'auth_url': auth_url, 'redirect_uri': redirect_uri}, status=status.HTTP_200_OK)



class OAuthLoginView(APIView):
    """
    POST /api/auth/oauth/<provider>/login/
    
    The frontend sends the authorization code (and optional redirect_uri).
    The backend exchanges the code for tokens and returns a JWT response.
    """
    permission_classes = [AllowAny]

    def post(self, request, provider):
        code = request.data.get('code')
        # Google's JS library uses 'postmessage' for popup flow
        redirect_uri = request.data.get('redirect_uri', 'postmessage')

        if not code:
            return Response(
                {'error': 'Authorization code is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate provider
        try:
            validate_provider(provider)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Step 1: Exchange code
        try:
            access_token = exchange_code_for_token(provider, code, redirect_uri)
        except Exception as e:
            return Response(
                {'error': f'Failed to exchange authorization code. {str(e)}'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Step 2: Fetch user info
        try:
            user_info = get_user_info(provider, access_token)
        except Exception:
            return Response(
                {'error': 'Failed to retrieve user information from the provider.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Step 3: Find or create user
        try:
            user = get_or_create_oauth_user(
                email=user_info['email'],
                first_name=user_info.get('first_name', ''),
                last_name=user_info.get('last_name', ''),
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Step 4: Return JWT
        refresh = RefreshToken.for_user(user)

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': LoginResponseSerializer(user).data,
        }, status=status.HTTP_200_OK)
