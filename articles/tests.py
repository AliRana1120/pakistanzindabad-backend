from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from .models import Article


class FeedImportTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="admin", password="secret", role="admin")

    @patch("articles.views.urlopen")
    def test_admin_can_import_articles_from_rss(self, mock_urlopen):
        class DummyResponse:
            def __init__(self, data):
                self._data = data

            def read(self):
                return self._data

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        mock_urlopen.return_value = DummyResponse(
            b"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<rss version=\"2.0\">
  <channel>
    <title>Sample Feed</title>
    <item>
      <title>Test headline</title>
      <description>Short excerpt</description>
      <link>https://example.com/test</link>
      <pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>"""
        )

        client = APIClient()
        client.force_authenticate(self.user)
        response = client.post(reverse("article-import"), {"source_url": "https://example.com/rss"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["imported"], 1)
        self.assertTrue(Article.objects.filter(title="Test headline").exists())

    @patch("articles.views.urlopen")
    def test_admin_can_import_default_feeds_without_pasting_a_url(self, mock_urlopen):
        class DummyResponse:
            def __init__(self, data):
                self._data = data

            def read(self):
                return self._data

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        mock_urlopen.return_value = DummyResponse(
            b"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<rss version=\"2.0\">
  <channel>
    <title>Sample Feed</title>
    <item>
      <title>Auto imported headline</title>
      <description>Short excerpt</description>
      <link>https://example.com/auto</link>
      <enclosure url=\"https://example.com/image.jpg\" type=\"image/jpeg\" />
    </item>
  </channel>
</rss>"""
        )

        client = APIClient()
        client.force_authenticate(self.user)
        response = client.post(reverse("article-import"), {})

        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.json()["imported"], 1)
        article = Article.objects.get(title="Auto imported headline")
        self.assertEqual(article.image_url, "https://example.com/image.jpg")
