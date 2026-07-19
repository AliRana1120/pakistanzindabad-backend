from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ArticleViewSet, EpaperViewSet, CommentAdminViewSet,rss_ticker

from articles.views import rss_feed
router = DefaultRouter()
router.register("epapers", EpaperViewSet, basename="epaper")
router.register("articles", ArticleViewSet, basename="article")
router.register("admin/comments", CommentAdminViewSet, basename="comment-admin")

urlpatterns = [
    path("", include(router.urls)),
    path("rss/", rss_feed, name="rss-feed"),
        path(
        "rss/ticker/",
        rss_ticker,
        name="rss-ticker"
    ),
]
