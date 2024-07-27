from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RegisterAPIView, LoginAPIView, ProfileAPIView, NotesAPIView, CustomUsersAPIView, MyTokenPairView, \
    VerifyAPIView

urlpatterns = [
    path('register/', RegisterAPIView.as_view()),
    path('verify/', VerifyAPIView.as_view()),
    path('login/', LoginAPIView.as_view()),
    path('profile/', ProfileAPIView.as_view()),
    path('notes/', NotesAPIView.as_view()),
    path('token/', MyTokenPairView.as_view()),
    path('token/refresh/', TokenRefreshView.as_view()),
    path('', CustomUsersAPIView.as_view()),
]
