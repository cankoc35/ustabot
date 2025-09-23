import json
from typing import Dict, Any

from entities import LIST_SCHEMA

from crawl4ai import (
    AsyncWebCrawler, 
    BrowserConfig, 
    CrawlerRunConfig, 
    CacheMode,
    VirtualScrollConfig,
    JsonCssExtractionStrategy
)

async def extract_from_google_maps(city_name: str, count: int) -> Dict[str, Any]:
    browser = BrowserConfig(
        headless=True, 
        viewport={"width": 1280, "height": 720}
    )
    virtual_config = VirtualScrollConfig(
        container_selector='[role="feed"]',
        scroll_count=count,                  
        scroll_by="container_height",
        wait_after_scroll=1,
    )
    strategy = JsonCssExtractionStrategy(schema=LIST_SCHEMA)
    run_config = CrawlerRunConfig(
        extraction_strategy=strategy, 
        cache_mode=CacheMode.BYPASS,
        virtual_scroll_config=virtual_config
    )

    async with AsyncWebCrawler(config=browser) as crawler:
        res = await crawler.arun(
            url=f"https://www.google.com/maps/search/{city_name}+en+iyi+oto+tamirciler", 
            config=run_config
        )

    raw = res.extracted_content
    data = json.loads(raw) if isinstance(raw, str) else raw

    # handle dict-or-list shapes
    items = data.get(LIST_SCHEMA["name"], []) if isinstance(data, dict) else (data if isinstance(data, list) else [])

    import re

    out = []
    for r in items:
        details = (r.get("details_block") or "").strip()

        # ----- star_rating -> float -----
        m_rating = re.search(r"\d+(?:[.,]\d+)?", str(r.get("star_rating", "")))
        star_rating = float(m_rating.group(0).replace(",", ".")) if m_rating else None

        # ----- number_of_comments -> int -----
        m_rev = re.search(r"\d+", str(r.get("number_of_comments", "")))
        if not m_rev and isinstance(r.get("star_rating"), str):
            m_rev = re.search(r"\((\d+)\)", r["star_rating"])
        number_of_comments = int(m_rev.group(1) if (m_rev and m_rev.lastindex) else m_rev.group(0)) if m_rev else None

        # ----- phone_number -> +90XXXXXXXXXX -----
        # matches: +90..., 0 5xx ..., (0232) 254 79 09, etc.
        m_phone = re.search(r"(\+90[\s\d]{10,}|0[\s\d]{10,}|(?:\(\d{3,4}\)\s*)?\d{3}\s*\d{2,3}\s*\d{2}\s*\d{2})", details)
        phone_number = None
        if m_phone:
            digits = re.sub(r"\D", "", m_phone.group(0))
            if digits.startswith("90") and len(digits) >= 12:
                phone_number = "+90" + digits[-10:]
            elif digits.startswith("0") and len(digits) == 11:
                phone_number = "+90" + digits[1:]
            elif len(digits) == 10:
                phone_number = "+90" + digits

        # ----- address -> first segment that looks like an address -----
        parts = [p.strip() for p in re.split(r"[•·⋅\n\|]+", details) if p.strip()]
        addr = None
        for p in parts:
            if re.search(r"(Mah(?:\.|allesi)?|Sk\.|Sok(?:\.|ak)?|Cd\.|Cadde|Bulv\.?|Blv\.?|No:?|Mevkii|Köy|İlçe|Caddesi|Sokağı)", p, re.I):
                addr = p
                break
        if addr:
            addr = addr.replace("Açık", "").replace("Kapalı", "").strip(" ,.-")
            addr = addr.__add__(city_name) if city_name not in addr else addr

        out.append({
            "repair_shop_name": (r.get("repair_shop_name") or "").strip(),
            "address": addr or city_name,
            "phone_number": phone_number,
            "star_rating": star_rating,
            "number_of_comments": number_of_comments,
        })

    return {"items": out}