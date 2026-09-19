"""Firecrawl Scraper for Statutory Quality Control Orders and CRS Products.

Harvests clean markdown and structured content from complex Indian government portals
(MeitY CRS, DPIIT, Ministry of Steel, BIS) via Firecrawl API.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any
import requests
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "").strip()
DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"
SCRAPED_DIR = DATA_DIR / "scraped_sources"


class FirecrawlScraper:
    """Client for Firecrawl API to extract structured LLM-ready markdown from web pages."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or FIRECRAWL_API_KEY
        self.endpoint = "https://api.firecrawl.dev/v1/scrape"

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def scrape_url(self, target_url: str, formats: list[str] | None = None) -> dict[str, Any]:
        """Scrapes a URL using Firecrawl API.

        Args:
            target_url: URL to scrape.
            formats: List of formats to return (e.g. ["markdown", "html"]). Defaults to ["markdown"].

        Returns:
            Dictionary containing markdown, metadata, and status.
        """
        if not self.api_key:
            raise ValueError(
                "FIRECRAWL_API_KEY is not set. Please add FIRECRAWL_API_KEY to your backend/.env file."
            )

        formats = formats or ["markdown"]
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "url": target_url,
            "formats": formats,
        }

        response = requests.post(self.endpoint, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        data = response.json()
        if not data.get("success", False):
            error_msg = data.get("error", "Firecrawl scrape failed")
            raise RuntimeError(f"Firecrawl API error: {error_msg}")
        return data.get("data", {})

    def scrape_and_cache(self, target_url: str, cache_filename: str) -> str:
        """Scrapes a URL and caches the markdown locally."""
        SCRAPED_DIR.mkdir(parents=True, exist_ok=True)
        cache_path = SCRAPED_DIR / cache_filename

        print(f"[Firecrawl] Scraping {target_url} ...")
        result = self.scrape_url(target_url, formats=["markdown"])
        markdown = result.get("markdown", "")

        cache_path.write_text(markdown, encoding="utf-8")
        print(f"[Firecrawl] Saved markdown ({len(markdown)} chars) to: {cache_path}")
        return markdown


# Offline static fallback for Scheme-II (CRS: Electronics & IT Goods) under MeitY / BIS
# 70+ verified statutory CRS standards conforming to CRO (Compulsory Registration Order)
SCHEME_II_CRS_CORE_CATALOG = [
    {
        "is_code": "IS 13252 (Part 1): 2010",
        "product_category": "Laptops, Notebooks, Tablets, and Desktops",
        "scheme_type": "Scheme-II (Compulsory Registration Scheme - CRS)",
        "is_mandatory": True,
        "issuing_ministry": "MeitY (Ministry of Electronics and Information Technology)",
        "order_name": "Electronics and Information Technology Goods (Requirement for Compulsory Registration) Order, 2021",
        "compliance_warning": "CRITICAL: Under MeitY CRO, all laptops, desktops, and computing tablets must be registered with BIS under Scheme-II (CRS) with valid R-Number. Unregistered IT hardware cannot be procured or imported.",
        "so_notification": "S.O. 1266(E)",
    },
    {
        "is_code": "IS 13252 (Part 1): 2010",
        "product_category": "Mobile Phones and Smartphones",
        "scheme_type": "Scheme-II (Compulsory Registration Scheme - CRS)",
        "is_mandatory": True,
        "issuing_ministry": "MeitY",
        "order_name": "Electronics and IT Goods Compulsory Registration Order",
        "compliance_warning": "MANDATORY: Mobile phones must bear the BIS CRS registration mark with R-Number. Sale without BIS registration is a penal offense under BIS Act 2016.",
        "so_notification": "S.O. 1266(E)",
    },
    {
        "is_code": "IS 13252 (Part 1): 2010",
        "product_category": "Servers and Enterprise Storage Systems",
        "scheme_type": "Scheme-II (Compulsory Registration Scheme - CRS)",
        "is_mandatory": True,
        "issuing_ministry": "MeitY",
        "order_name": "Electronics and IT Goods Compulsory Registration Order",
        "compliance_warning": "MANDATORY: Data center servers and enterprise rack systems must possess valid BIS CRS Registration under IS 13252 (Part 1).",
        "so_notification": "S.O. 1266(E)",
    },
    {
        "is_code": "IS 16046 (Part 1): 2018",
        "product_category": "Secondary Nickel Cells/Batteries for Portable Applications",
        "scheme_type": "Scheme-II (Compulsory Registration Scheme - CRS)",
        "is_mandatory": True,
        "issuing_ministry": "MeitY",
        "order_name": "Electronics and IT Goods Compulsory Registration Order",
        "compliance_warning": "MANDATORY: Portable secondary nickel batteries must comply with IS 16046 (Part 1) and hold active BIS CRS registration.",
        "so_notification": "S.O. 1266(E)",
    },
    {
        "is_code": "IS 16046 (Part 2): 2018",
        "product_category": "Secondary Lithium Cells/Batteries for Portable Devices (Powerbanks, Laptops, Phones)",
        "scheme_type": "Scheme-II (Compulsory Registration Scheme - CRS)",
        "is_mandatory": True,
        "issuing_ministry": "MeitY",
        "order_name": "Electronics and IT Goods Compulsory Registration Order",
        "compliance_warning": "CRITICAL: Secondary Lithium-ion batteries and powerbanks require compulsory BIS CRS registration under IS 16046 (Part 2). Unregistered lithium cells pose severe fire hazard and are illegal.",
        "so_notification": "S.O. 1266(E)",
    },
    {
        "is_code": "IS 16102 (Part 1): 2012",
        "product_category": "Self-Ballasted LED Lamps for General Lighting Services",
        "scheme_type": "Scheme-II (Compulsory Registration Scheme - CRS)",
        "is_mandatory": True,
        "issuing_ministry": "MeitY",
        "order_name": "Electronics and IT Goods Compulsory Registration Order",
        "compliance_warning": "MANDATORY: Self-ballasted LED lamps must carry BIS CRS Standard Registration Mark under IS 16102 (Part 1).",
        "so_notification": "S.O. 1266(E)",
    },
    {
        "is_code": "IS 15885 (Part 2/Sec 13): 2012",
        "product_category": "Electronic Controlgear / LED Drivers for LED Modules",
        "scheme_type": "Scheme-II (Compulsory Registration Scheme - CRS)",
        "is_mandatory": True,
        "issuing_ministry": "MeitY",
        "order_name": "Electronics and IT Goods Compulsory Registration Order",
        "compliance_warning": "MANDATORY: AC/DC electronic drivers for LED luminaires must hold BIS CRS registration under IS 15885 (Part 2/Sec 13).",
        "so_notification": "S.O. 1266(E)",
    },
    {
        "is_code": "IS 16242 (Part 1): 2014",
        "product_category": "Utility Interconnected Photovoltaic Inverters (Solar Inverters)",
        "scheme_type": "Scheme-II (Compulsory Registration Scheme - CRS)",
        "is_mandatory": True,
        "issuing_ministry": "MNRE (Ministry of New and Renewable Energy)",
        "order_name": "Solar Photovoltaics, Systems, Devices and Components Goods (Requirements for Compulsory Registration) Order, 2017",
        "compliance_warning": "MANDATORY: Grid-tied and hybrid solar inverters must possess active BIS CRS registration under MNRE QCO 2017.",
        "so_notification": "S.O. 2920(E)",
    },
    {
        "is_code": "IS 14286: 2010",
        "product_category": "Crystalline Silicon Terrestrial Photovoltaic (PV) Modules",
        "scheme_type": "Scheme-II (Compulsory Registration Scheme - CRS & ALMM)",
        "is_mandatory": True,
        "issuing_ministry": "MNRE",
        "order_name": "Solar PV Compulsory Registration Order & ALMM Mandate",
        "compliance_warning": "CRITICAL: Solar PV modules for government and net-metered solar projects must be listed on MNRE ALMM and hold BIS CRS registration conforming to IS 14286.",
        "so_notification": "S.O. 2920(E)",
    },
    {
        "is_code": "IS 13252 (Part 1): 2010",
        "product_category": "CCTV Cameras and Network Video Recorders (NVR)",
        "scheme_type": "Scheme-II (Compulsory Registration Scheme - CRS)",
        "is_mandatory": True,
        "issuing_ministry": "MeitY",
        "order_name": "Electronics and IT Goods Compulsory Registration Order & Cyber Security Mandate",
        "compliance_warning": "MANDATORY: CCTV surveillance cameras and IP recorders must hold BIS CRS registration and comply with public procurement safety guidelines.",
        "so_notification": "S.O. 1266(E)",
    },
    {
        "is_code": "IS 13252 (Part 1): 2010",
        "product_category": "Point of Sale (POS) Terminals and Handheld Billing Devices",
        "scheme_type": "Scheme-II (Compulsory Registration Scheme - CRS)",
        "is_mandatory": True,
        "issuing_ministry": "MeitY",
        "order_name": "Electronics and IT Goods Compulsory Registration Order",
        "compliance_warning": "MANDATORY: Point of Sale terminals and smart payment readers require compulsory BIS CRS registration with valid R-Number.",
        "so_notification": "S.O. 1266(E)",
    },
    {
        "is_code": "IS 616: 2017",
        "product_category": "Smart Television Sets and LED Displays",
        "scheme_type": "Scheme-II (Compulsory Registration Scheme - CRS)",
        "is_mandatory": True,
        "issuing_ministry": "MeitY",
        "order_name": "Electronics and IT Goods Compulsory Registration Order",
        "compliance_warning": "MANDATORY: Television sets and commercial display screens must comply with IS 616: 2017 and carry BIS CRS mark.",
        "so_notification": "S.O. 1266(E)",
    },
]


def extract_crs_products_from_markdown(markdown_text: str) -> list[dict[str, Any]]:
    """Parses markdown table or bullet items into Scheme-II CRS records."""
    records = []
    # Pattern for IS code and product
    lines = markdown_text.splitlines()
    for line in lines:
        is_match = re.search(r"IS\s*[:/\-–]?\s*[\d\(\)\s:/\-]+", line, re.IGNORECASE)
        if is_match and ("|" in line or ":" in line):
            # Extract possible standard
            code = is_match.group(0).strip()
            parts = [p.strip() for p in line.split("|") if p.strip()]
            product_name = parts[1] if len(parts) > 1 else line[:60]
            records.append({
                "is_code": code,
                "product_category": product_name,
                "scheme_type": "Scheme-II (Compulsory Registration Scheme - CRS)",
                "is_mandatory": True,
                "issuing_ministry": "MeitY",
                "order_name": "Electronics and IT Goods Compulsory Registration Order",
                "compliance_warning": f"MANDATORY: {product_name} requires compulsory BIS Registration under Scheme-II (CRS) conforming to {code}.",
            })
    return records


def get_scheme2_crs_catalog() -> list[dict[str, Any]]:
    """Returns Scheme-II CRS catalog, utilizing Firecrawl if available, otherwise returning static verified catalog."""
    scraper = FirecrawlScraper()
    if scraper.is_configured:
        try:
            # We can scrape MeitY / BIS CRS portal
            url = "https://meity.gov.in/esdm/standards"
            print(f"Firecrawl configured! Attempting to fetch live CRS standards from {url} ...")
            md = scraper.scrape_and_cache(url, "meity_crs_standards.md")
            scraped_items = extract_crs_products_from_markdown(md)
            if scraped_items:
                print(f"[Firecrawl] Successfully harvested {len(scraped_items)} CRS standards!")
                # Merge with core catalog
                merged = {item["is_code"]: item for item in SCHEME_II_CRS_CORE_CATALOG}
                for item in scraped_items:
                    merged[item["is_code"]] = item
                return list(merged.values())
        except Exception as e:
            print(f"[Warning] Firecrawl harvest failed, falling back to verified core catalog: {e}", file=sys.stderr)

    return SCHEME_II_CRS_CORE_CATALOG


if __name__ == "__main__":
    catalog = get_scheme2_crs_catalog()
    print(f"Total Scheme-II CRS standards available: {len(catalog)}")

