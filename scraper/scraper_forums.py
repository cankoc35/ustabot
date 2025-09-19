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
class ForumComment(BaseModel):
    username: str = Field(None, alias="username")
    comment_text: Optional[str] = Field(None, alias="comment_text")

class ForumCommentTable(BaseModel):
    items: List[ForumComment]

INSTRUCTION = """
Extract visible forum comments and return ONLY username and comment_text per comment. 
Clean text by removing quoted replies, signatures, “edited/düzenlendi” markers, and link clutter; 
trim whitespace. If a field is missing, set null. 
Output ONLY JSON with a top-level 'items' array matching the schema—no summaries, no invented data; 
one array item per comment.
"""


EXTRACT_URL = "https://forum.donanimhaber.com/izmir-de-otomobil-ozel-servis-tavsiyesi--147690758"

def build_crawler_config_for_ollama() -> CrawlerRunConfig:
    return CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        page_timeout=90_000,
        extraction_strategy=LLMExtractionStrategy(
            llm_config=LLMConfig(
                provider="ollama/llama3.2:3b", # llama3.2:3b - deepseek-r1:7b
                base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
                api_token=None,
                temperature=0,
            ),
            schema=ForumCommentTable.model_json_schema(),
            extraction_type="schema",
            instruction=INSTRUCTION)
    )

async def extract_with_ollama(url: str) -> Dict:
    browser = BrowserConfig(headless=True, java_script_enabled=True)
    config = build_crawler_config_for_ollama()
    async with AsyncWebCrawler(config=browser) as crawler:
        print(f"Extracting from {url} ...")
        result = await crawler.arun(url=url, config=config)
        # Always validate JSON
        return json.loads(result.extracted_content or "{}")

async def main():
    data = await extract_with_ollama(EXTRACT_URL)  
    print(json.dumps(data, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())
