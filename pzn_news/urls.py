from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from django.http import JsonResponse

urlpatterns = [
    path("test/", lambda request: JsonResponse({"ok": True})),
    path("api/test/", lambda request: JsonResponse({"ok": True, "service": "backend"})),
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("accounts.urls")),
    path("api/v1/", include("articles.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
