import unittest
from unittest.mock import patch

from backend.services.news_service import NewsService, interest_key


class NewsEvidenceTests(unittest.TestCase):
    def test_evidence_preserves_source_details_and_terms(self):
        topic = {"source_url": "https://example.com/story", "source_name": "Example", "summary": "fallback"}
        text = "The RAG pipeline uses v2.1. It reduces latency by 25 percent. The deployment has a 16GB memory limit."
        with patch.object(NewsService, "_safe_fetch_text", return_value=(text, "extracted")):
            evidence = NewsService().extract_evidence(topic)
        self.assertEqual("extracted", evidence["extraction_status"])
        self.assertIn("16GB", evidence["extracted_text"])
        self.assertIn("RAG", evidence["evidence"]["technical_terms"])
        self.assertEqual("https://example.com/story", evidence["evidence"]["source_url"])

    def test_interest_key_is_order_independent(self):
        self.assertEqual(interest_key(["RAG", "部署"]), interest_key(["部署", "RAG"]))


if __name__ == "__main__":
    unittest.main()
