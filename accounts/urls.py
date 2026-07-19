from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import LoginView, RegisterView, MeView, AdminSetupOpenView, ChangeUsernameView, ChangePasswordView

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("register/", RegisterView.as_view(), name="register"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", MeView.as_view(), name="me"),
    path("setup-open/", AdminSetupOpenView.as_view(), name="setup-open"),
    path("auth/change-username/", ChangeUsernameView.as_view(), name="change-username"),
    path("auth/change-password/", ChangePasswordView.as_view(), name="change-password"),
]
