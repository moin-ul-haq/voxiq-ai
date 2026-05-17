from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'password']

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['email'],  # username = email
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
        )
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'first_name',
            'last_name',
            'email',
            'bio',
            'current_role',
            'experience_level',
            'resume',
            'onboarding_complete',
            'created_at',
        ]
        read_only_fields = ['id', 'email', 'resume', 'onboarding_complete', 'created_at']


class ResumeUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['resume']

    def validate_resume(self, value):
        if not value.name.endswith('.pdf'):
            raise serializers.ValidationError("Only PDF files are allowed.")
        if value.size > 5 * 1024 * 1024:  # 5MB limit
            raise serializers.ValidationError("File size must be under 5MB.")
        return value


class LoginResponseSerializer(serializers.ModelSerializer):
    """Used only for shaping login response — not for input."""
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'onboarding_complete']