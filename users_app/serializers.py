from django.utils import timezone
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import CustomUser, AUTH_TYPE, Note
from django.core.mail import send_mail
from config.settings import EMAIL_HOST_USER
from shared_app.utils import validate_email_or_phone, send_sms_vonage


class RegisterSerializer(ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    username = serializers.CharField(required=True, validators=[UniqueValidator(queryset=CustomUser.objects.all())])
    password = serializers.CharField(write_only=True, required=True)

    def __init__(self, *args, **kwargs):
        super(RegisterSerializer, self).__init__(*args, **kwargs)
        self.fields['email_or_phone'] = serializers.CharField(required=False)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'password', 'auth_type', 'email', 'phone_number']

        extra_kwargs = {
            'auth_type': {'required': False},
        }

    def validate(self, data):
        if CustomUser.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError("Username already exists")
        email_or_phone = data['email_or_phone']
        print('1) email_or_phone: ', email_or_phone)
        auth_type = validate_email_or_phone(data['email_or_phone'])
        if auth_type == AUTH_TYPE.email:
            data.update({'email': email_or_phone, 'auth_type': auth_type})
            if CustomUser.objects.filter(email=data['email_or_phone']).exists():
                raise serializers.ValidationError("Email already exist")
        elif auth_type == AUTH_TYPE.phone:
            data.update({'phone_number': email_or_phone, 'auth_type': auth_type})
            if CustomUser.objects.filter(phone_number=data['email_or_phone']).exists():
                raise serializers.ValidationError("Phone number already exist")
        else:
            raise serializers.ValidationError("Invalid email or phone number")
        print('2) validated data from validate: ', data)
        return data

    def create(self, validated_data):
        validated_data.pop('email_or_phone')
        print('3) validated data from create: ', validated_data)
        user = super(RegisterSerializer, self).create(validated_data)
        try:
            print('4) user password hashed!!!')
            user.set_password(validated_data.get('password'))
        except Exception as e:
            print('4) user password did not hashed!!!: ', e)
            raise serializers.ValidationError('password did not hashed!!!')
        if user.auth_type == AUTH_TYPE.email:
            code = user.create_verify_code(AUTH_TYPE.email)
            print('5) auth_type is email, code: ', code)
            send_mail(subject='We congratulate you on registration',
                      message=f"Welcome to our site {user.username}, your code: {code}",
                      from_email=EMAIL_HOST_USER,
                      recipient_list=[user.email, ],
                      fail_silently=False)
        else:
            code = user.create_verify_code(AUTH_TYPE.phone)
            print(f"5) auth_type is phone, code: {code}")
            response = send_sms_vonage(to_number=user.phone_number, body=f"Welcome to our App {user.username}, your "
                                                                         f"code: {code}")
            print(f"6) response: {response}")
        user.save()

        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class VerificationSerializer(serializers.Serializer):
    code = serializers.CharField()


class CustomUserSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    auth_type = serializers.CharField(read_only=True)
    date_joined = serializers.DateTimeField(read_only=True)
    created_time = serializers.DateTimeField(read_only=True)
    updated_time = serializers.DateTimeField(read_only=True)
    days_since_joined = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'full_name', 'days_since_joined', 'photo', 'first_name', 'last_name', 'email',
                  'phone_number', 'date_of_birth', 'gender', 'auth_type', 'province', 'bio', 'date_joined',
                  'created_time', 'updated_time', ]

    @staticmethod
    def get_days_since_joined(obj):
        return (timezone.now() - obj.date_joined).days


class NoteSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    owner = CustomUserSerializer(read_only=True)
    created_time = serializers.DateTimeField(read_only=True)
    updated_time = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Note
        fields = ['id', 'owner', 'text', 'isPinned', 'sequence_number', 'category', 'created_time', 'updated_time']

    def validate(self, data):
        if not data['text']:
            raise serializers.ValidationError("Text field can not be empty.")
        return data

    def create(self, validated_data):
        owner = validated_data.get('owner')
        note = validated_data.get('text')
        if Note.objects.filter(owner=owner, text=note).exists():
            raise serializers.ValidationError("Note already exist")
        created_note = Note.objects.create(owner=owner, text=note)
        created_note.save()
        return created_note

    def update(self, instance, validated_data):
        instance.text = validated_data.get('text', instance.text)
        instance.save()
        return instance


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['auth_type'] = user.auth_type

        return token


class CustomUsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone_number']
        extra_kwargs = {
            'username': {'read_only': True},
            'email': {'read_only': True},
            'phone_number': {'read_only': True},
        }
