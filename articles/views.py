import json
import re
import xml.etree.ElementTree as ET
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from django.db.models import Q
from django.http import JsonResponse
from django.utils.text import slugify
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from articles.tasks import REDIS_KEY_PREFIX, _redis, refresh_rss_category

from .models import Article, Comment, Epaper
from .permissions import IsAdminOrReadOnly
from .serializers import (
    ArticleDetailSerializer,
    ArticleListSerializer,
    ArticleWriteSerializer,
    CommentCreateSerializer,
    CommentSerializer,
    EpaperSerializer,
)

DEFAULT_FEED_URLS = [
    # BBC Urdu
    "https://feeds.bbci.co.uk/urdu/rss.xml",

    # Dawn
    "https://www.dawn.com/feeds/home",

    # The News International
    "https://www.thenews.com.pk/rss/1/10",

    # Business Recorder
    "https://fp.brecorder.com/feed/",

    # Express Tribune
    "https://tribune.com.pk/feed",

    # Associated Press of Pakistan (APP)
    "https://www.app.com.pk/feed/",

    # Reuters World
    "https://www.reutersagency.com/feed/?best-topics=world&post_type=best",

    # Al Jazeera
    "https://www.aljazeera.com/xml/rss/all.xml",
]
def _extract_image_url_from_text(text):
    if not text:
        return None
    match = re.search(r"https?://[^\s\"'<>]+(?:jpg|jpeg|png|webp|gif|avif)", text, re.I)
    if not match:
        return None
    return match.group(0).rstrip(").,;")


def _extract_image_url_from_feed_item(item):
    for child in item.iter():
        tag = child.tag.split("}", 1)[-1].lower()
        if tag in {"enclosure", "media:content", "media:thumbnail", "thumbnail", "image"}:
            for attr_name in ("url", "href", "src"):
                value = child.attrib.get(attr_name)
                if value and value.startswith(("http://", "https://")):
                    return value
        for attr_name in ("url", "href", "src"):
            value = child.attrib.get(attr_name)
            if value and value.startswith(("http://", "https://")) and value.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif")):
                return value
    for child in item.iter():
        if child.text and child.text.strip().startswith(("http://", "https://")):
            return _extract_image_url_from_text(child.text)
    return None


class ArticleViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["category", "featured", "published"]
    search_fields = ["title", "excerpt", "content", "tags"]
    ordering_fields = ["created_at", "updated_at"]
    ordering = ["-created_at"]
    lookup_field = "slug"

    def get_queryset(self):
        qs = Article.objects.all()
        # Public users only see published articles
        if not (self.request.user and self.request.user.is_authenticated):
            qs = qs.filter(published=True)
        # Tag filter
        tag = self.request.query_params.get("tag")
        if tag:
            qs = qs.filter(tags__contains=[tag])
        return qs

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ArticleWriteSerializer
        if self.action == "retrieve":
            return ArticleDetailSerializer
        return ArticleListSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=False, methods=["post"], url_path="import", url_name="import")
    def import_articles(self, request):
        source_url = request.data.get("source_url") or request.data.get("feed_url")
        sources = [source_url] if source_url else list(DEFAULT_FEED_URLS)

        created = []
        tried_sources = []

        for feed_url in sources:
            feed_url = (feed_url or "").strip()
            if not feed_url:
                continue
            tried_sources.append(feed_url)
            try:
                with urlopen(feed_url) as response:
                    raw = response.read()
            except (URLError, HTTPError, ValueError):
                continue

            items = []
            headers = getattr(response, "headers", None)
            content_type = headers.get_content_type() if headers is not None and hasattr(headers, "get_content_type") else ""
            if content_type == "application/json" or str(feed_url).lower().endswith(".json"):
                data = json.loads(raw.decode("utf-8"))
                if isinstance(data, list):
                    items = data
                elif isinstance(data, dict):
                    for key in ("items", "articles", "posts", "results"):
                        if isinstance(data.get(key), list):
                            items = data[key]
                            break
            else:
                try:
                    root = ET.fromstring(raw)
                except ET.ParseError:
                    continue
                if root.tag.endswith("rss"):
                    items = [
                        {
                            "title": item.findtext("title") or "",
                            "excerpt": item.findtext("description") or "",
                            "content": item.findtext("description") or "",
                            "url": item.findtext("link") or "",
                            "published_at": item.findtext("pubDate") or "",
                            "image_url": _extract_image_url_from_feed_item(item),
                        }
                        for item in root.findall(".//item")
                    ]
                elif root.tag.endswith("feed"):
                    items = [
                        {
                            "title": entry.findtext("{*}title") or "",
                            "excerpt": entry.findtext("{*}summary") or entry.findtext("{*}content") or "",
                            "content": entry.findtext("{*}content") or entry.findtext("{*}summary") or "",
                            "url": entry.findtext("{*}link") or "",
                            "published_at": entry.findtext("{*}updated") or "",
                            "image_url": _extract_image_url_from_feed_item(entry),
                        }
                        for entry in root.findall("{*}entry")
                    ]

            for item in items[:10]:
                if not isinstance(item, dict):
                    continue
                title = (item.get("title") or item.get("headline") or item.get("name") or "").strip()
                if not title:
                    continue
                excerpt = (item.get("excerpt") or item.get("summary") or item.get("description") or "").strip()
                content = (item.get("content") or item.get("body") or excerpt or "").strip()
                image_url = (
                    item.get("image")
                    or item.get("image_url")
                    or item.get("thumbnail")
                    or item.get("thumbnail_url")
                    or item.get("cover")
                    or item.get("cover_url")
                    or item.get("featured_image")
                    or item.get("imageUrl")
                )
                if not image_url:
                    image_url = _extract_image_url_from_text(content) or _extract_image_url_from_text(excerpt)
                summary_val = item.get("summary") or item.get("description") or ""
                payload = {
                    "slug": slugify(title, allow_unicode=True)[:120] or "imported-article",
                    "title": title,
                    "excerpt": excerpt[:500] if excerpt else title,
                    "content": content[:20000] if content else title,
                    "summary": summary_val[:500] if summary_val else (excerpt[:500] if excerpt else title),
                    "category": item.get("category") or "پاکستان",
                    "image_url": image_url or None,
                    "featured": False,
                    "published": True,
                    "tags": [],
                }
                serializer = ArticleWriteSerializer(data=payload, context={"request": request})
                if serializer.is_valid():
                    serializer.save(author=request.user)
                    created.append(title)

        return Response({"imported": len(created), "created": created, "sources": tried_sources})

    @action(detail=False, methods=["get"])
    def ticker(self, request):
        """GET /api/articles/ticker/ — latest 8 headlines"""
        qs = Article.objects.filter(published=True).values("id", "slug", "title", "category")[:8]
        return Response(list(qs))

    @action(detail=False, methods=["get"])
    def search(self, request):
        """GET /api/articles/search/?q=term"""
        q = request.query_params.get("q", "").strip()
        if not q:
            return Response([])
        qs = Article.objects.filter(published=True).filter(
            Q(title__icontains=q) | Q(excerpt__icontains=q) | Q(content__icontains=q)
        )[:30]
        return Response(ArticleListSerializer(qs, many=True).data)

    @action(detail=True, methods=["get"])
    def related(self, request, slug=None):
        """GET /api/articles/<slug>/related/"""
        article = self.get_object()
        qs = Article.objects.filter(published=True, category=article.category).exclude(pk=article.pk)[:4]
        return Response(ArticleListSerializer(qs, many=True).data)

    @action(detail=True, methods=["get", "post"])
    def comments(self, request, slug=None):
        article = self.get_object()
        if request.method == "GET":
            comments = article.comments.filter(approved=True)
            return Response(CommentSerializer(comments, many=True).data)
        # POST — create a comment (anyone can submit)
        serializer = CommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(article=article)
        return Response({"detail": "آپ کا تبصرہ جائزے کے بعد شائع کیا جائے گا۔"}, status=status.HTTP_201_CREATED)


class EpaperViewSet(viewsets.ModelViewSet):
    serializer_class = EpaperSerializer
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    ordering = ["-edition_date"]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def get_queryset(self):
        qs = Epaper.objects.all()
        if not (self.request.user and self.request.user.is_authenticated):
            qs = qs.filter(published=True)
        return qs


class CommentAdminViewSet(viewsets.ModelViewSet):
    """Admin-only: approve/delete comments"""
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_admin():
            return Comment.objects.none()
        return Comment.objects.all().select_related("article")

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        comment = self.get_object()
        comment.approved = True
        comment.save()
        return Response({"detail": "منظور شدہ"})

@api_view(["GET"])
@permission_classes([AllowAny])
def rss_feed(request):
    try:
        category = request.GET.get("category", "all")

        try:
            limit = int(request.GET.get("limit", 9))
        except (TypeError, ValueError):
            limit = 9

        redis_key = f"{REDIS_KEY_PREFIX}{category}"

        # Test Redis
        cached = _redis.get(redis_key)

        if cached:
            if isinstance(cached, bytes):
                cached = cached.decode("utf-8")

            return JsonResponse(
                json.loads(cached)[:limit],
                safe=False
            )

        # Test Celery
        task = refresh_rss_category.delay(category)

        return JsonResponse({
            "status": "loading",
            "task_id": task.id,
            "message": "RSS refresh started"
        })

    except Exception as exc:
        import traceback

        return JsonResponse(
            {
                "error": type(exc).__name__,
                "message": str(exc),
                "traceback": traceback.format_exc(),
            },
            status=500,
        )
        
        
@api_view(["GET"])
@permission_classes([AllowAny])
def rss_ticker(request):
    limit = int(request.GET.get("limit", 8))
    redis_key = f"{REDIS_KEY_PREFIX}all"

    cached = _redis.get(redis_key)
    if not cached:
        return JsonResponse([], safe=False)

    articles = json.loads(cached)
    ticker = [
        {
            "title": item.get("title"),
            "category": item.get("category"),
            "link": item.get("link"),
        }
        for item in articles[:limit]
    ]
    return JsonResponse(ticker, safe=False)