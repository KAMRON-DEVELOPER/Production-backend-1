from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import AuthStatus, CustomUser, CustomUserConfirmation, Note, Tab
from .serializers import (
    CustomUserSerializer,
    CustomUsersSerializer,
    LoginSerializer,
    MyTokenObtainPairSerializer,
    NoteSerializer,
    RegisterSerializer,
    VerificationSerializer, TabSerializer,
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
    permission_classes = [permissions.IsAuthenticated, ]

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

            user.auth_status = AuthStatus.done
            user.save()

            confirmation = CustomUserConfirmation.objects.get(user=user, code=code)
            confirmation.is_confirmed = True
            confirmation.save()
            data = user.token()
            print(f"data >> {data}")
            return Response(data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)


class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny, ]

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
    permission_classes = [permissions.IsAuthenticated, ]

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
    permission_classes = [permissions.IsAuthenticated, ]

    def get(self, request):
        user = request.user
        profile_serializer = CustomUserSerializer(user, many=False)
        print(f"profile >> {user}")
        return Response(profile_serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        user = request.user


class TabAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        tabs = request.user.tabs.all()
        tabs_serializer = TabSerializer(tabs, many=True)
        tabs = tabs_serializer.data
        for tab in tabs:
            tab.pop('owner', None)
        print(f"user >> {request.user}, tabs_serializer >> {tabs_serializer.data}")
        return Response(tabs, status=status.HTTP_200_OK)

    def post(self, request):
        print(f"user >> {request.user}, data >> {request.data}")
        tab_serializer = TabSerializer(data=request.data, context={'owner': request.user})
        if tab_serializer.is_valid():
            tab_serializer.save()
            tab = tab_serializer.data
            tab.pop('owner', None)
            return Response(tab, status=status.HTTP_201_CREATED)
        return Response(tab_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        tab_id = request.data.get("id")
        print(f"user >> {request.user}\n tab_id >> {tab_id}")
        tab = Tab.objects.get(id=tab_id, owner=request.user)
        serializer = TabSerializer(tab, data=request.data, context={"owner": request.user}, many=False)
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        note = Note.objects.get(id=request.data["id"])
        note.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class NotesAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        notes = request.user.notes.filter(category=None)
        print(f'user >> {request.user}\n notes >> {notes}')
        notes_serializer = NoteSerializer(notes, many=True)
        notes = notes_serializer.data
        for note in notes:
            note.pop("owner", None)
        return Response(notes, status=status.HTTP_200_OK)

    def post(self, request):
        print(f"data >> {request.data}\n user >> {request.user}")
        serializer = NoteSerializer(data=request.data, context={"owner": request.user}, many=False)
        if serializer.is_valid():
            serializer.save()
            new_note = serializer.data
            new_note.pop('owner', None)
            return Response(new_note, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        user = request.user
        print(f"user >> {user}\n tab_id >> {request.data.get('id')}")
        tab = Tab.objects.get(id=request.data.get("id"), owner=request.user)
        serializer = TabSerializer(tab, data=request.data, context={"owner": request.user}, many=False)
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        tab = Tab.objects.get(id=request.data["id"])
        tab.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CustomUsersAPIView(APIView):
    permission_classes = [permissions.AllowAny, ]

    def get(self, request):
        users = CustomUser.objects.all()
        users_serializers = CustomUsersSerializer(users, many=True)
        return Response(users_serializers.data, status=status.HTTP_200_OK)

