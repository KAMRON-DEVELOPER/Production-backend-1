from django.urls import path
from .views import RegisterAPIView, LoginAPIView, VerifyAPIView, ProfileAPIView, NotesAPIView, MyTokenObtainPairView, \
    CustomUsersAPIView

urlpatterns = [
    path('register/', RegisterAPIView.as_view()),
    path('login/', LoginAPIView.as_view()),
    path('verify/', VerifyAPIView.as_view()),
    path('profile/', ProfileAPIView.as_view()),
    path('notes/', NotesAPIView.as_view()),
    path('', CustomUsersAPIView.as_view()),
]
