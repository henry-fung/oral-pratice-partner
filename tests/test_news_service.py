import unittest
from unittest.mock import MagicMock, patch

from backend.services.news_service import NewsService


class NewsServiceTests(unittest.TestCase):
    def test_parses_and_normalizes_rss_headlines(self):
        response = MagicMock()
        response.read.return_value = b'''<?xml version="1.0"?><rss><channel><item>
            <title>Example headline</title><link>https://example.com/article</link>
            <description>&lt;b&gt;A concise summary&lt;/b&gt;</description>
            <source>Example News</source><pubDate>Mon, 21 Sep 2026 12:00:00 GMT</pubDate>
        </item></channel></rss>'''
        with patch("backend.services.news_service.urlopen") as urlopen:
            urlopen.return_value.__enter__.return_value = response
            topics = NewsService().fetch_topics()

        self.assertEqual(1, len(topics))
        self.assertEqual("Example headline", topics[0]["headline"])
        self.assertEqual("A concise summary", topics[0]["summary"])
        self.assertEqual("Example News", topics[0]["source_name"])


if __name__ == "__main__":
    unittest.main()
