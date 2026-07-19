from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from .serializers import RegisterSerializer, UserSerializer

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class AdminSetupOpenView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        open = not User.objects.filter(role="admin").exists() and not User.objects.filter(is_superuser=True).exists()
        return Response({"open": open})

# ── ADD these to your Django backend ─────────────────────────────────────────
# pzn_news/views.py (or wherever your auth views are)

from django.contrib.auth import update_session_auth_hash
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status


class ChangeUsernameView(APIView):
    """PATCH /api/auth/change-username/"""
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        username = request.data.get("username", "").strip()
        if not username:
            return Response({"detail": "یوزر نیم خالی ہے"}, status=400)
        if len(username) < 3:
            return Response({"detail": "یوزر نیم کم از کم 3 حروف کا ہونا چاہیے"}, status=400)

        from django.contrib.auth import get_user_model
        User = get_user_model()
        if User.objects.filter(username=username).exclude(pk=request.user.pk).exists():
            return Response({"detail": "یہ یوزر نیم پہلے سے استعمال میں ہے"}, status=400)

        request.user.username = username
        request.user.save(update_fields=["username"])
        return Response({"username": username})


class ChangePasswordView(APIView):
    """POST /api/auth/change-password/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        old_password = request.data.get("old_password", "")
        new_password = request.data.get("new_password", "")

        if not request.user.check_password(old_password):
            return Response({"old_password": ["موجودہ پاس ورڈ غلط ہے"]}, status=400)
        if len(new_password) < 8:
            return Response({"detail": "نیا پاس ورڈ کم از کم 8 حروف کا ہونا چاہیے"}, status=400)

        request.user.set_password(new_password)
        request.user.save()
        # Keep session active on web (JWT — tokens still valid until expiry)
        return Response({"detail": "پاس ورڈ کامیابی سے تبدیل ہو گیا"})


# ── Also add file_size to Epaper model ───────────────────────────────────────
# In your epapers/models.py, add:
#
# file_size = models.BigIntegerField(null=True, blank=True)
#
# Then run: python manage.py makemigrations && python manage.py migrate
#
# In your epapers/views.py, when saving a PDF file, set file_size:
#
# if 'pdf_file' in request.FILES:
#     f = request.FILES['pdf_file']
#     instance.file_size = f.size
#     # save file to storage...


# ── Add URL patterns ─────────────────────────────────────────────────────────
# In your urls.py add:
#
# path("auth/change-username/", ChangeUsernameView.as_view(), name="change-username"),
# path("auth/change-password/", ChangePasswordView.as_view(), name="change-password"),
