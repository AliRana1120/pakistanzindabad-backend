from django.contrib import admin
from .models import Article, Epaper, Comment

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "featured", "published", "created_at"]
    list_filter = ["category", "featured", "published"]
    search_fields = ["title", "excerpt"]
    prepopulated_fields = {"slug": ("title",)}

@admin.register(Epaper)
class EpaperAdmin(admin.ModelAdmin):
    list_display = ["title", "edition_date", "published"]

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["name", "article", "approved", "created_at"]
    list_filter = ["approved"]
    actions = ["approve_comments"]

    def approve_comments(self, request, queryset):
        queryset.update(approved=True)
    approve_comments.short_description = "منتخب تبصرے منظور کریں"
