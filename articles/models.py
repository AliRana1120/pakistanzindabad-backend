import uuid
from django.db import models
from django.utils.text import slugify


CATEGORY_CHOICES = [
    ("سیاست", "سیاست"),
    ("کھیل", "کھیل"),
    ("کاروبار", "کاروبار"),
    ("ٹیکنالوجی", "ٹیکنالوجی"),
    ("بین الاقوامی", "بین الاقوامی"),
    ("پاکستان", "پاکستان"),
]


class Article(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(max_length=300, unique=True, allow_unicode=True)
    title = models.CharField(max_length=500)
    excerpt = models.TextField()
    content = models.TextField()
    summary = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    image_url = models.URLField(blank=True, null=True, max_length=1000)
    featured = models.BooleanField(default=False)
    published = models.BooleanField(default=False)
    tags = models.JSONField(default=list, blank=True)
    author = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articles",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title, allow_unicode=True) or str(self.id)[:8]
            slug = base
            n = 1
            while Article.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Epaper(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=300)
    edition_date = models.DateField()
    pdf_url = models.URLField(max_length=1000)
    cover_url = models.URLField(blank=True, null=True, max_length=1000)
    published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-edition_date"]

    def __str__(self):
        return f"{self.title} — {self.edition_date}"


class Comment(models.Model):
    """NEW: Reader comments on articles"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="comments")
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    body = models.TextField(max_length=1000)
    approved = models.BooleanField(default=False)  # admin must approve
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.name} on {self.article.title[:40]}"
