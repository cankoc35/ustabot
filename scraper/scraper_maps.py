import asyncio, json
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

from crawl4ai import (
    AsyncWebCrawler, 
    BrowserConfig, 
    CrawlerRunConfig, 
    CacheMode,
    VirtualScrollConfig,
    JsonCssExtractionStrategy
)

class RepairShop(BaseModel):
    repair_shop_name: str
    address: Optional[str] = None
    phone_number: Optional[str] = None
    star_rating: Optional[float] = None
    number_of_comments: Optional[int] = None

class RepairShopTable(BaseModel):
    items: List[RepairShop]

LIST_SCHEMA = {
    "name": "Google Maps Repair Shops",
    "baseSelector": (
        "[role='feed'] [role='article'][data-result-index], "   # 1) structural
        "[role='feed'] [data-result-index], "                   # 2) looser structural
        "[role='feed'] .Nv2PK"                                  # 3) old obfuscated card class
    ),
    "fields": [
        {"name": "repair_shop_name",
         "selector": ".qBF1Pd.fontHeadlineSmall, .qBF1Pd, .fontHeadlineSmall, h3",
         "type": "text"},
        {"name": "place_url",
         "selector": "a.hfpxzc[href*='/place/']",
         "type": "link"},
        {"name": "star_rating",
         "selector": ".MW4etd[aria-hidden='true'], .ZkP5Je[aria-label*='yıldız'], .ZkP5Je[aria-label*='star']",
         "type": "text"},
        {"name": "number_of_comments",
         "selector": ".UY7F9, span[aria-label*='yorum'], span[aria-label*='review'], span[aria-label*='reviews']",
         "type": "text"},
        {"name": "phone_number",
         "selector": ".UaQhfb.fontBodyMedium .Usdlk, a[href^='tel:']",
         "type": "text"},
        {"name": "address",
         "selector": ".UaQhfb.fontBodyMedium span[aria-hidden='true'] + span",
         "type": "text"},
        {"name": "details_block",
         "selector": ".UaQhfb.fontBodyMedium",
         "type": "text"},
    ],
}

EXTRACT_URL = "https://www.google.com/maps/search/izmir+en+iyi+oto+tamirciler"

async def extract_with_css(url: str) -> Dict[str, Any]:
    browser = BrowserConfig(
        headless=True, 
        viewport={"width": 1280, "height": 720}
    )
    virtual_config = VirtualScrollConfig(
        container_selector='[role="feed"]',
        scroll_count=20,                  
        scroll_by="container_height",
        wait_after_scroll=2,
    )
    strategy = JsonCssExtractionStrategy(schema=LIST_SCHEMA)
    run_config = CrawlerRunConfig(
        extraction_strategy=strategy, 
        cache_mode=CacheMode.BYPASS,
        virtual_scroll_config=virtual_config
    )

    async with AsyncWebCrawler(config=browser) as crawler:
        res = await crawler.arun(url, config=run_config)

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


        out.append({
            "repair_shop_name": (r.get("repair_shop_name") or "").strip(),
            "address": addr or None,
            "phone_number": phone_number,
            "star_rating": star_rating,
            "number_of_comments": number_of_comments,
        })

    return {"items": out}

if __name__ == "__main__":
    data = asyncio.run(extract_with_css(EXTRACT_URL))
    print(json.dumps(data, ensure_ascii=False, indent=2))


