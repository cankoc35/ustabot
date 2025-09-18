import os, json, re, asyncio
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
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

INSTRUCTION = (
    "Extract all visible repair shops from the results list panel. "
    "Return ONLY one JSON object matching the schema. Use null/[] if unknown."
)

EXTRACT_URL = "https://www.google.com/maps/search/izmir+en+iyi+oto+tamirciler"

def _first_json_blob(s: str) -> Optional[str]:
    if not s: return None
    s = s.strip()
    s = re.sub(r"^```(?:json)?\s*|\s*```$", "", s)
    depth = 0; start = None
    for i, ch in enumerate(s):
        if ch == "{":
            if depth == 0: start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                return s[start:i+1]
    return None

async def extract_with_ollama(url: str) -> Dict[str, Any]:
    browser = BrowserConfig(headless=True, java_script_enabled=True)
    
    vscroll = VirtualScrollConfig(
        container_selector="div[role='feed']",  # Google Maps results list
        scroll_count=80,                        # try 80–120 for long lists
        scroll_by="container_height",
        wait_after_scroll=1.0                   # give network time per step
    )

    run = CrawlerRunConfig(
        virtual_scroll_config=vscroll,          
        cache_mode=CacheMode.BYPASS,
        page_timeout=150_000,
        extraction_strategy=LLMExtractionStrategy(
            llm_config=LLMConfig(
                provider="ollama/llama3.2:3b",   
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
    blob = _first_json_blob(raw) or raw
    data = json.loads(blob) 

    RepairShopTable.model_validate(data)
    print(f"Extracted {len(data.get('items', []))} items")
    return data

if __name__ == "__main__":
    print(asyncio.run(extract_with_ollama(EXTRACT_URL)))
