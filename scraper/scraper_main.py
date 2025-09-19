import os, json, re, asyncio
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, ValidationError
from datetime import datetime
from crawl4ai import (
    AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode,
    LLMExtractionStrategy, LLMConfig, VirtualScrollConfig
)

# ----- schema -----
class RepairShop(BaseModel):
    repair_shop_name: str
    address: Optional[str] = None
    phone_number: Optional[str] = None
    star_rating: Optional[float] = None
    number_of_comments: Optional[int] = None

class RepairShopTable(BaseModel):
    items: List[RepairShop]
    
cities_and_districts = {
    "city1": "İzmir",
    "districts1": ["Bornova", "Konak", "Karşıyaka", "Gaziemir", "Bayraklı", "Çiğli", "Balçova", "Narlıdere", "Buca", "Aliağa","Seferihisar","Torbalı","Menemen","Dikili","Urla","Foça","Karaburun","Menderes","Selçuk"],
    "city2": "İstanbul",
    "districts2": ["Kadıköy", "Beşiktaş", "Üsküdar", "Bakırköy", "Esenyurt", "Sarıyer", "Maltepe", "Pendik", "Kartal", "Ataşehir","Çekmeköy","Beylikdüzü","Bahçelievler","Bağcılar","Güngören","Zeytinburnu","Bayrampaşa","Esenler","Sultangazi","Arnavutköy","Başakşehir"],
    "city3": "Ankara",
    "districts3": ["Çankaya", "Keçiören", "Yenimahalle", "Mamak", "Altındağ", "Sincan", "Etimesgut", "Pursaklar", "Gölbaşı", "Kızılcahamam","Akyurt","Polatlı","Beypazarı","Nallıhan","Çubuk","Elmadağ","Haymana","Kalecik","Şereflikoçhisar","Kahramankazan","Ayaş"],
}        

INSTRUCTION = (
    "You are extracting from a Google Maps results list (left panel). "
    "Return JSON that VALIDATES against this schema and NOTHING else (no prose, no markdown fences):\n"
    f"{json.dumps(RepairShopTable.model_json_schema(), ensure_ascii=False)}\n"
    'Output exactly one object of the form: {"items":[{...}]}. '
    "Use null for unknown fields. Do not add extra keys.\n"
)

EXTRACT_URL = "https://www.google.com/maps/search/izmir+en+iyi+oto+tamirciler"

def _first_json_blob(s: str) -> Optional[str]:
    if not s:
        return None
    s = s.strip()
    s = re.sub(r"^```(?:json)?\s*|\s*```$", "", s)
    depth = 0
    start = None
    for i, ch in enumerate(s):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                return s[start:i+1]
    return None

def _coerce_shop_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    # Map common alt keys to canonical fields
    return {
        "repair_shop_name": d.get("repair_shop_name") or d.get("name") or d.get("title"),
        "address": d.get("address") or d.get("addr") or d.get("location"),
        "phone_number": d.get("phone_number") or d.get("phone") or d.get("tel"),
        "star_rating": d.get("star_rating") or d.get("rating"),
        "number_of_comments": d.get("number_of_comments") or d.get("reviews") or d.get("review_count"),
    }

def normalize_extraction_to_table(obj: Any) -> Dict[str, Any]:
    """
    Convert any plausible LLM output into {"items": [RepairShop-like dicts]}.
    """
    if obj is None:
        return {"items": []}

    if isinstance(obj, str):
        try:
            obj = json.loads(obj)
        except json.JSONDecodeError:
            return {"items": []}

    if isinstance(obj, dict):
        # Already correct?
        if "items" in obj:
            items = obj["items"]
            if isinstance(items, dict):
                items = [items]
            elif not isinstance(items, list):
                items = []
            return {"items": [_coerce_shop_dict(x) for x in items if isinstance(x, dict)]}

        # Single-object case
        if "repair_shop_name" in obj or "name" in obj or "title" in obj:
            return {"items": [_coerce_shop_dict(obj)]}

        # Alternative top-level keys the LLM might choose
        for key in ("shops", "results", "repair_shops", "data"):
            if key in obj:
                val = obj[key]
                if isinstance(val, dict):
                    val = [val]
                if isinstance(val, list):
                    return {"items": [_coerce_shop_dict(x) for x in val if isinstance(x, dict)]}

        return {"items": []}

    if isinstance(obj, list):
        return {"items": [_coerce_shop_dict(x) for x in obj if isinstance(x, dict)]}

    return {"items": []}

async def extract_with_ollama(url: str) -> Dict[str, Any]:
    browser = BrowserConfig(headless=True, java_script_enabled=True)

    vscroll = VirtualScrollConfig(
        container_selector="#pane .m6QErb[aria-label][role='region'], #pane [role='feed'], [role='feed']",
        scroll_count=160,                 # deeper, virtualized list needs more
        scroll_by="container_height",
        wait_after_scroll=1.0,
    )

    run = CrawlerRunConfig(
        virtual_scroll_config=vscroll,
        cache_mode=CacheMode.BYPASS,
        page_timeout=150_000,
        extraction_strategy=LLMExtractionStrategy(
            llm_config=LLMConfig(
                provider="ollama/llama3.1:8b",   # try a larger model if you have it
                base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
                api_token=None,
                temperature=0,
            ),
            schema=RepairShopTable.model_json_schema(),
            extraction_type="schema",
            instruction=INSTRUCTION,
        ),
    )

    async with AsyncWebCrawler(config=browser) as crawler:
        result = await crawler.arun(url=url, config=run)

    if not getattr(result, "success", False):
        raise RuntimeError(getattr(result, "error_message", "crawl failed"))

    raw = result.extracted_content or ""
    # Save exactly what the LLM returned for debugging
    with open("last_raw_extraction.txt", "w", encoding="utf-8") as f:
        f.write(raw)

    blob = _first_json_blob(raw) or raw
    try:
        data = json.loads(blob) if isinstance(blob, str) else blob
    except json.JSONDecodeError:
        data = {}

    # Normalize and validate; never crash here
    data = normalize_extraction_to_table(data)
    try:
        validated = RepairShopTable.model_validate(data)
    except ValidationError as e:
        print("Validation failed; coercing to empty table.\n", e)
        validated = RepairShopTable(items=[])

    # Persist
    payload = validated.model_dump(mode="json")
    filename = f"repair_shops_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"Extracted {len(payload.get('items', []))} items → {filename}")
    return payload

if __name__ == "__main__":
    asyncio.run(extract_with_ollama(EXTRACT_URL))
