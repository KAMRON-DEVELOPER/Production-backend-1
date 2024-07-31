from django.core.mail import send_mail
from django.utils import timezone
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from config.settings import EMAIL_HOST_USER
from shared_app.utils import send_sms_vonage, validate_email_or_phone
from .models import AuthType, CustomUser, Note, Tab


class RegisterSerializer(ModelSerializer):
    def __init__(self, *args, **kwargs):
        super(RegisterSerializer, self).__init__(*args, **kwargs)
        self.fields["email_or_phone"] = serializers.CharField(required=True)

    class Meta:
        model = CustomUser
        fields = ["id", "username", "password", "auth_type", "email", "phone_number", ]

        extra_kwargs = {
            "id": {"required": False, "read_only": True},
            "username": {"required": True},
            "password": {"required": True, "write_only": True},
            "auth_type": {"required": False},
            "email": {"required": False},
            "phone_number": {"required": False},
        }

    def validate(self, data):
        username = data["username"]
        password = data["password"]
        email_or_phone = data["email_or_phone"]
        if CustomUser.objects.filter(username=username).exists():
            raise serializers.ValidationError("Username already exists")
        print("1) email_or_phone: ", email_or_phone)
        auth_type = validate_email_or_phone(email_or_phone)
        if auth_type == AuthType.email:
            data.update({"email": email_or_phone, "auth_type": auth_type})
            if CustomUser.objects.filter(email=data["email_or_phone"]).exists():
                raise serializers.ValidationError("Email already exist")
        elif auth_type == AuthType.phone:
            data.update({"phone_number": email_or_phone, "auth_type": auth_type})
            if CustomUser.objects.filter(phone_number=data["email_or_phone"]).exists():
                raise serializers.ValidationError("Phone number already exist")
        else:
            raise serializers.ValidationError("Invalid email or phone number")
        if (password == ''):
            raise serializers.ValidationError('password field is required')
        print("2) validated data from validate: ", data)
        return data

    def create(self, validated_data):
        validated_data.pop("email_or_phone")
        print("3) validated data from create: ", validated_data)
        user = super(RegisterSerializer, self).create(validated_data)
        try:
            print("4) user password hashed!!!")
            user.set_password(validated_data.get("password"))
        except Exception as e:
            print("4) user password did not hashed!!!: ", e)
            raise serializers.ValidationError("password did not hashed!!!")
        if user.auth_type == AuthType.email:
            code = user.create_verify_code(AuthType.email)
            print("5) auth_type is email, code: ", code)
            send_mail(
                subject="We congratulate you on registration",
                message=f"Welcome to our site {user.username}, your code: {code}",
                from_email=EMAIL_HOST_USER,
                recipient_list=[
                    user.email,
                ],
                fail_silently=False,
            )
        else:
            code = user.create_verify_code(AuthType.phone)
            print(f"5) auth_type is phone, code: {code}")
            response = send_sms_vonage(
                to_number=user.phone_number,
                body=f"Welcome to our App {user.username}, your code: {code}",
            )
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
    tabs = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "username",
            "full_name",
            "days_since_joined",
            "photo",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "date_of_birth",
            "gender",
            "auth_type",
            "province",
            "bio",
            "date_joined",
            "created_time",
            "updated_time",
            "tabs"
        ]

    @staticmethod
    def get_days_since_joined(obj):
        return (timezone.now() - obj.date_joined).days

    @staticmethod
    def get_tabs(obj):
        tabs = []
        categories = obj.note_categories.all()
        for category in categories:
            tabs.append({"category_name": f"{category.name}",
                         "category_sequence_number": f"{category.tab_sequence_number}"
                         })
        return tabs


class LoginDataSerializer(CustomUserSerializer):
    access_token = serializers.CharField(read_only=True)
    refresh_token = serializers.CharField(read_only=True)

    class Meta(CustomUserSerializer.Meta):
        fields = CustomUserSerializer.Meta.fields + ["access_token", "refresh_token"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        tokens = instance.token()
        representation['access_token'] = tokens['access_token']
        representation['refresh_token'] = tokens['refresh_token']
        return representation


class TabSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    owner = CustomUserSerializer(read_only=True)
    created_time = serializers.DateTimeField(read_only=True)
    updated_time = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Tab
        fields = ["id", "owner", "name", "tab_sequence_number", "created_time", "updated_time"]

    def validate(self, data):
        owner = self.context.get('owner')
        name = data.get("name")
        print(f"data >{data}\n owner > {owner}\n name > {name}")
        if not owner:
            raise serializers.ValidationError("Tab owner must provided")
        elif not name:
            raise serializers.ValidationError("Tab name must provided")
        elif Tab.objects.filter(owner=owner, name=name).exists():
            raise serializers.ValidationError("Tab already exists")
        data['owner'] = owner
        return data

    def create(self, validated_data):
        new_tab = Tab.objects.create(**validated_data)
        print(f"new_note_category >> {new_tab}")
        return new_tab

    def update(self, instance, validated_data):
        print(f"validated_data >> {validated_data}")
        instance.name = validated_data.get("name", instance.name)
        instance.tab_sequence_number = validated_data.get("tab_sequence_number", instance.tab_sequence_number)
        instance.save()
        return instance


class NoteSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    owner = CustomUserSerializer(read_only=True)
    category = serializers.PrimaryKeyRelatedField(queryset=Tab.objects.all(), required=False)
    created_time = serializers.DateTimeField(read_only=True)
    updated_time = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Note
        fields = [
            "id",
            "owner",
            "body",
            "isPinned",
            "note_sequence_number",
            "category",
            "created_time",
            "updated_time",
        ]

    def validate(self, data):
        owner = self.context.get('owner')
        body = data.get("body")
        category = data.get("category")
        print(f"owner >> {owner}\n body >> {body}\n category >> {category}, data >> {data}")
        if not owner:
            raise serializers.ValidationError("Owner of the note must be provided")
        elif not body:
            raise serializers.ValidationError("Note body must be provided")
        elif Note.objects.filter(owner=owner, body=body).exists():
            raise serializers.ValidationError("Note already exist")
        elif category and not Tab.objects.filter(id=category.id, owner=owner).exists():
            raise serializers.ValidationError("Category must belongs to owner of the note")
        data['owner'] = owner
        return data

    def create(self, validated_data):
        created_note = Note.objects.create(**validated_data)
        print(f"created_note >> {created_note}")
        return created_note

    def update(self, instance, validated_data):
        print(f"validated_data >> {validated_data}")
        instance.body = validated_data.get("body", instance.body)
        instance.category = validated_data.get("category", instance.category)
        instance.isPinned = validated_data.get("isPinned", instance.isPinned)
        instance.note_sequence_number = validated_data.get("note_sequence_number", instance.note_sequence_number)
        instance.save()
        return instance


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["username"] = user.username

        return token


class CustomUsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["username", "email", "phone_number"]
        extra_kwargs = {
            "username": {"read_only": True},
            "email": {"read_only": True},
            "phone_number": {"read_only": True},
        }
