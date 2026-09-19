"""Scrape.do Client for Government Portals and Anti-Bot Protected BIS Pages.

Handles proxy rotation, geo-targeting (India), and optional headless JS rendering
via Scrape.do API.
"""
from __future__ import annotations

import os
import sys
import urllib.parse
from pathlib import Path
from typing import Any
import requests
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

SCRAPE_DO_TOKEN = os.getenv("SCRAPE_DO_TOKEN", "").strip()


class ScrapeDoClient:
    """Client for Scrape.do Web Scraping API."""

    def __init__(self, token: str | None = None):
        self.token = token or SCRAPE_DO_TOKEN
        self.base_url = "http://api.scrape.do"

    @property
    def is_configured(self) -> bool:
        return bool(self.token)

    def fetch_url(
        self,
        target_url: str,
        render_js: bool = False,
        geo_code: str = "in",
        timeout: int = 60,
    ) -> str:
        """Fetches web page content using Scrape.do proxy gateway.

        Args:
            target_url: The public URL to scrape.
            render_js: Whether to execute JavaScript using a headless browser.
            geo_code: ISO 2-letter country code for proxy routing (default: 'in').
            timeout: HTTP request timeout in seconds.

        Returns:
            The raw HTML content returned by the server.
        """
        if not self.token:
            raise ValueError(
                "SCRAPE_DO_TOKEN is not set. Please add SCRAPE_DO_TOKEN to your backend/.env file."
            )

        params: dict[str, Any] = {
            "token": self.token,
            "url": target_url,
        }
        if render_js:
            params["render"] = "true"
        if geo_code:
            params["geoCode"] = geo_code

        response = requests.get(self.base_url, params=params, timeout=timeout)
        response.raise_for_status()
        return response.text


def main():
    client = ScrapeDoClient()
    if not client.is_configured:
        print("[Warning] SCRAPE_DO_TOKEN is not configured in backend/.env")
        return

    test_url = "https://www.bis.gov.in"
    print(f"Testing Scrape.do connection against {test_url} ...")
    try:
        html = client.fetch_url(test_url, render_js=False)
        print(f"[Success] Fetched {len(html)} bytes via Scrape.do proxy.")
    except Exception as e:
        print(f"[Error] Scrape.do request failed: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()

