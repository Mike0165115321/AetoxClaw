import pytest
from unittest.mock import MagicMock, patch
from aetox.tools.web_scraper import WebPulseScraper

class TestWebScraper:
    @pytest.fixture
    def scraper(self):
        return WebPulseScraper()

    def test_fetch_content_success(self, scraper):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body><h1>Hello World</h1><p>This is a test.</p></body></html>"
        mock_response.apparent_encoding = "utf-8"
        
        with patch("httpx.Client.get", return_value=mock_response):
            result = scraper.execute({
                "action": "fetch_content",
                "url": "https://example.com",
                "max_length": 100
            })
            
        assert result["status"] == "success"
        assert "Hello World" in result["output"]
        assert "This is a test" in result["output"]

    def test_fetch_content_failure(self, scraper):
        with patch("httpx.Client.get", side_effect=Exception("Connection Error")):
            result = scraper.execute({
                "action": "fetch_content",
                "url": "https://badurl.com"
            })
            
        assert result["status"] == "failure"
        assert "Failed to fetch" in result["error"]

    def test_extract_links(self, scraper):
        mock_html = """
        <html>
            <body>
                <a href="/page1">Page 1</a>
                <a href="https://example.com/page2">Page 2</a>
                <a href="https://other.com">External</a>
            </body>
        </html>
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = mock_html
        mock_response.apparent_encoding = "utf-8"
        
        with patch("httpx.Client.get", return_value=mock_response):
            result = scraper.execute({
                "action": "extract_links",
                "url": "https://example.com",
                "filter": "Page"
            })
            
        assert result["status"] == "success"
        assert "page1" in result["output"]
        assert "page2" in result["output"]
        assert "External" not in result["output"] # Scraper filters external by default

    def test_extract_by_selector(self, scraper):
        mock_html = "<html><body><div class='target'>Special Content</div></body></html>"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = mock_html
        mock_response.apparent_encoding = "utf-8"
        
        with patch("httpx.Client.get", return_value=mock_response):
            result = scraper.execute({
                "action": "extract_by_selector",
                "url": "https://example.com",
                "selector": ".target"
            })
            
        assert result["status"] == "success"
        assert "Special Content" in result["output"]

    def test_summarize_page(self, scraper):
        # Scraper summarize is extractive, it picks sentences
        mock_html = "<html><body>" + ". ".join([f"Sentence {i}" for i in range(10)]) + "</body></html>"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = mock_html
        mock_response.apparent_encoding = "utf-8"
        
        with patch("httpx.Client.get", return_value=mock_response):
            result = scraper.execute({
                "action": "summarize_page",
                "url": "https://example.com"
            })
            
        assert result["status"] == "success"
        assert "Sentence 0" in result["output"]
