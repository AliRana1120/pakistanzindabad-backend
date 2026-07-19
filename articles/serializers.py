from django.conf import settings
from django.core.files.storage import default_storage
from rest_framework import serializers
from .models import Article, Epaper, Comment


def _build_media_url(request, stored_path):
    if not stored_path:
        return None
    if request is not None:
        return request.build_absolute_uri(settings.MEDIA_URL + stored_path)
    return settings.MEDIA_URL + stored_path


class ArticleListSerializer(serializers.ModelSerializer):
    """Lightweight — used for list/ticker/search"""
    class Meta:
        model = Article
        fields = [
            "id", "slug", "title", "excerpt", "summary",
            "category", "image_url", "featured", "published",
            "tags", "created_at", "updated_at",
        ]


class ArticleDetailSerializer(serializers.ModelSerializer):
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            "id", "slug", "title", "excerpt", "content", "summary",
            "category", "image_url", "featured", "published",
            "tags", "created_at", "updated_at", "comment_count",
        ]

    def get_comment_count(self, obj):
        return obj.comments.filter(approved=True).count()


class ArticleWriteSerializer(serializers.ModelSerializer):
    image_file = serializers.ImageField(required=False, write_only=True)

    class Meta:
        model = Article
        fields = [
            "slug", "title", "excerpt", "content", "summary",
            "category", "image_url", "image_file", "featured", "published", "tags",
        ]

    def create(self, validated_data):
        image_file = validated_data.pop("image_file", None)
        request = self.context.get("request")
        if image_file:
            stored_path = default_storage.save(f"articles/{image_file.name}", image_file)
            validated_data["image_url"] = _build_media_url(request, stored_path)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        image_file = validated_data.pop("image_file", None)
        request = self.context.get("request")
        if image_file:
            stored_path = default_storage.save(f"articles/{image_file.name}", image_file)
            validated_data["image_url"] = _build_media_url(request, stored_path)
        return super().update(instance, validated_data)


class EpaperSerializer(serializers.ModelSerializer):
    pdf_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    cover_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    pdf_file = serializers.FileField(required=False, write_only=True)
    cover_file = serializers.ImageField(required=False, write_only=True)

    class Meta:
        model = Epaper
        fields = ["id", "title", "edition_date", "pdf_url", "cover_url", "pdf_file", "cover_file", "published", "created_at", "updated_at"]

    def validate(self, attrs):
        pdf_url = attrs.get("pdf_url")
        cover_url = attrs.get("cover_url")
        pdf_file = attrs.get("pdf_file")
        cover_file = attrs.get("cover_file")

        if not pdf_url and not pdf_file:
            raise serializers.ValidationError({"pdf_url": "PDF URL یا PDF فائل ضروری ہے۔"})
        if cover_url and cover_file:
            attrs["cover_url"] = cover_url
        return attrs

    def create(self, validated_data):
        pdf_file = validated_data.pop("pdf_file", None)
        cover_file = validated_data.pop("cover_file", None)
        request = self.context.get("request")
        if pdf_file:
            stored_path = default_storage.save(f"epapers/{pdf_file.name}", pdf_file)
            validated_data["pdf_url"] = _build_media_url(request, stored_path)
        if cover_file:
            stored_path = default_storage.save(f"epapers/{cover_file.name}", cover_file)
            validated_data["cover_url"] = _build_media_url(request, stored_path)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        pdf_file = validated_data.pop("pdf_file", None)
        cover_file = validated_data.pop("cover_file", None)
        request = self.context.get("request")
        if pdf_file:
            stored_path = default_storage.save(f"epapers/{pdf_file.name}", pdf_file)
            validated_data["pdf_url"] = _build_media_url(request, stored_path)
        if cover_file:
            stored_path = default_storage.save(f"epapers/{cover_file.name}", cover_file)
            validated_data["cover_url"] = _build_media_url(request, stored_path)
        return super().update(instance, validated_data)


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["id", "name", "body", "created_at"]  # email hidden from public


class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["name", "email", "body"]
