import os, json, asyncio
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

from crawl4ai import (
    AsyncWebCrawler, 
    BrowserConfig, 
    CrawlerRunConfig, 
    CacheMode,
    LLMExtractionStrategy, 
    LLMConfig, 
    VirtualScrollConfig,
    AdaptiveCrawler
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
    "Return JSON that VALIDATES against this schema and NOTHING else:\n"
    f"{json.dumps(RepairShopTable.model_json_schema(), ensure_ascii=False)}\n"
    'Output exactly one object of the form: {"items":[{...}]}. '
    "Treat every visible list card as one item. Use null for unknown fields."
)

EXTRACT_URL = "https://www.google.com/maps/search/izmir+en+iyi+oto+tamirciler"
QUERY = "izmir en iyi oto tamirciler"

LLM_MODEL = "ollama/llama3.2:3b"
HOST = "OLLAMA_HOST"
HOST_URL = "http://localhost:11434"

async def extract_with_ollama(url: str) -> Dict[str, Any]:
    browser_config = BrowserConfig(
        headless=True, 
        java_script_enabled=True,
        enable_stealth=True
    )

    vscroll_config = VirtualScrollConfig(
        container_selector="#pane [role=feed]",
        scroll_count=120,      
        scroll_by="container_height",
        wait_after_scroll=1.2,
    )

    crawler_config = CrawlerRunConfig(
        css_selector="#pane [role=feed]",
        process_iframes=True,
        remove_overlay_elements=True,
        virtual_scroll_config=vscroll_config,
        cache_mode=CacheMode.BYPASS,
        page_timeout=150_000,
        extraction_strategy=LLMExtractionStrategy(
            llm_config=LLMConfig(
                provider=LLM_MODEL, 
                base_url=os.getenv(HOST, HOST_URL),
                api_token=None,
                temperature=0,
            ),
            schema=RepairShopTable.model_json_schema(),
            extraction_type="schema",
            instruction=INSTRUCTION
        ),
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        adaptive_crawler = AdaptiveCrawler(
            crawler,
            max_pages=1,
            top_k_links=0,
        )
        
        adaptive_result = await adaptive_crawler.digest(
            url,
            query=QUERY,
        )
        
        # Print adaptive crawling stats
        adaptive_crawler.print_stats()
        print(f"Achieved {adaptive_crawler.confidence:.0%} confidence")

        # Perform extraction
        result = await crawler.arun(url, crawler_config)        
        print(json.dumps(result.extracted_content, ensure_ascii=False, indent=2))
        return result.extracted_content

if __name__ == "__main__":
    asyncio.run(extract_with_ollama(EXTRACT_URL))
