from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import AUTH_STATUS, CustomUser, CustomUserConfirmation, Note
from .serializers import (
    CustomUserSerializer,
    CustomUsersSerializer,
    LoginSerializer,
    MyTokenObtainPairSerializer,
    NoteSerializer,
    RegisterSerializer,
    VerificationSerializer, LoginDataSerializer,
)


class RegisterAPIView(APIView):
    permission_classes = [
        permissions.AllowAny,
    ]

    def post(self, request):
        register_data = request.data
        print(f"1) request data: {register_data}")
        serializer = RegisterSerializer(data=register_data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.save()
            data = user.token()
            print(f'data >> {data}')
            return Response(data, status=status.HTTP_201_CREATED)
        return Response(
            {"error": f"{serializer.errors}"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class VerifyAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated,]

    def post(self, request):
        print(f"1) request.data >> {request.data}")
        serializer = VerificationSerializer(data=request.data)
        try:
            user = request.user
            print(f"2) request.user >> {request.user}")
        except:
            return Response({'error': 'request.user did not work!!!'}, status=status.HTTP_401_UNAUTHORIZED)

        if serializer.is_valid():
            code = serializer.validated_data.get('code')
            print(f"3) code >> {code}")

            if not CustomUserConfirmation.objects.filter(user=user, code=code).exists():
                return Response({"error": "Invalid verification code."}, status=status.HTTP_404_NOT_FOUND)

            user.auth_status = AUTH_STATUS.done
            user.save()

            confirmation = CustomUserConfirmation.objects.get(user=user, code=code)
            confirmation.is_confirmed = True
            confirmation.save()
            data = user.token()
            print(f"data >> {data}")
            return Response(data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)


class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny,]

    def post(self, request):
        print(f"1) request.data >> {request.data}")
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data.get("username")
            password = serializer.validated_data.get("password")
            print(f"2) username >> {username}")
            try:
                user = CustomUser.objects.get(username=username)
                print(f"3) user >> {user}")
            except:
                return Response(
                    {"error": f"Sorry, I couldn't find an account with that username."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if not user.check_password(password):
                print("4) user password is not correct")
                return Response(
                    {"error": "Sorry, that password isn't right."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            data = user.token()
            print(f"data >> {data}")
            return Response(data, status=status.HTTP_200_OK)
        return Response(
            {"error": serializer.errors, "message": "Sorry about that, my bad!"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated,]

    def post(self, request):
        print(f"1) request.data >> {request.data}")
        try:
            refresh_token = request.data["refresh_token"]
            print(f"refresh_token >> {refresh_token}")
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_200_OK)
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class MyTokenPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class ProfileAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated,]

    def get(self, request):
        print(f"1) request headers >> {request.headers}")
        print(f"2) request >> {request}")
        print(f"3) request.user >> {request.user}")
        try:
            user = request.user
        except Exception as e:
            print(f'user error >> {e}')
        user_serializer = CustomUserSerializer(user, many=False)
        print(f"4) user_serializer.data >> {user_serializer.data}")
        return Response(user_serializer.data, status=status.HTTP_200_OK)


class NotesAPIView(APIView):
    permission_classes = [permissions.AllowAny,]

    def get(self, request):
        user = request.user
        notes = user.notes.all()
        note_serializer = NoteSerializer(notes, many=True)
        return Response(note_serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        print(f"1) request: {request}")
        user = request.user
        print(f"1) request: {user}")
        serializer = NoteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        notes = Note.objects.all()
        note = Note.objects.get(id=request.data["id"])
        notes_serializer = NoteSerializer(notes, many=True)
        try:
            print(f"note is deleted: {note}")
            note.delete()
        except:
            print("node did not delete!")
            return Response(notes_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(notes_serializer.data, status=status.HTTP_200_OK)


class CustomUsersAPIView(APIView):
    permission_classes = [permissions.AllowAny, ]

    def get(self, request):
        users = CustomUser.objects.all()
        users_serializers = CustomUsersSerializer(users, many=True)
        return Response(users_serializers.data, status=status.HTTP_200_OK)
