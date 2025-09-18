import os, asyncio, json
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode,
    LLMExtractionStrategy,
    LLMConfig,
)

# ----- Define a strict schema for what you want back -----
class RepairShop(BaseModel):
    repair_shop_name: str = Field(..., alias="repair_shop_name")
    address: Optional[str] = Field(None, alias="address")
    phone_number: Optional[str] = Field(None, alias="phone_number")
    star_rating: Optional[float] = Field(None, alias="star_rating")
    number_of_comments: Optional[int] = Field(None, alias="number_of_comments")

class RepairShopTable(BaseModel):
    items: List[RepairShop]

INSTRUCTION = """
Extract every mentioned repair shop and its name, address, phone number, star rating (out of 5), and number of comments.
Return ONLY JSON matching the provided schema.
If a field is missing on the page, set it to null.
"""

EXTRACT_URL = "https://www.google.com/maps/search/izmir+en+iyi+oto+tamirciler"

def build_crawler_config_for_ollama() -> CrawlerRunConfig:
    return CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        page_timeout=90_000,
        extraction_strategy=LLMExtractionStrategy(
            llm_config=LLMConfig(
                provider="ollama/deepseek-r1:7b",
                base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
                api_token=None,
                temperature=0,
            ),
            schema=RepairShopTable.model_json_schema(),
            extraction_type="schema",
            instruction=INSTRUCTION,
        ),
    )

async def extract_with_ollama(url: str) -> Dict:
    browser = BrowserConfig(headless=True, java_script_enabled=True)
    config = build_crawler_config_for_ollama()
    async with AsyncWebCrawler(config=browser) as crawler:
        result = await crawler.arun(url=url, config=config)
        # Always validate JSON
        return json.loads(result.extracted_content or "{}")

async def main():
    data = await extract_with_ollama(EXTRACT_URL)  
    print(json.dumps(data, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())
