import os, asyncio, pathlib, re
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

EXTRACT_URL = "https://forum.donanimhaber.com/izmir-de-otomobil-ozel-servis-tavsiyesi--147690758"
OUTDIR = "out"
OUTFILE = "page_raw.html"
OUTFILE_CLEAN = "page_clean.html"  # Crawl4AI’nin temizlediği sürüm

def build_crawler_config_for_raw() -> CrawlerRunConfig:
    return CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,   # her seferinde taze çek
        page_timeout=90_000,           # ms
        scan_full_page=True,           # sayfayı tam tara
        process_iframes=True,          # iframe içeriklerini de dahil et
        excluded_tags=["iframe","script","style","noscript"],
        # css_selector="main, article, #content, .post, .entry"
    )

async def fetch_raw_html(url: str):
    browser = BrowserConfig(
        browser_type="chromium",
        headless=True,
        java_script_enabled=True,
        verbose=False,
    )
    config = build_crawler_config_for_raw()

    async with AsyncWebCrawler(config=browser) as crawler:
        print(f"Fetching {url} ...")
        result = await crawler.arun(url=url, config=config)

        raw_html   = getattr(result, "html", "") or ""
        clean_html = getattr(result, "cleaned_html", "") or ""

        out = pathlib.Path(OUTDIR); out.mkdir(parents=True, exist_ok=True)
        (out / OUTFILE).write_text(raw_html, encoding="utf-8")
        if clean_html:
            (out / OUTFILE_CLEAN).write_text(clean_html, encoding="utf-8")

        print(f"Saved raw HTML -> {out / OUTFILE}")
        if clean_html:
            print(f"Saved cleaned HTML -> {out / OUTFILE_CLEAN}")

        # --- Sürüm güvenli alan okuma ---
        status = (
            getattr(result, "status_code", None)
            or getattr(result, "http_status", None)
        )
        final_url = getattr(result, "final_url", None) or getattr(result, "url", None)
        success = getattr(result, "success", None)
        error   = getattr(result, "error", None) or getattr(result, "error_message", None)

        return {
            "status": status,          # None olabilir; sorun değil
            "url": final_url,
            "success": success,
            "error": error,
            "raw_len": len(raw_html),
            "clean_len": len(clean_html),
        }

def dh_to_printable(url: str) -> str:
    m = re.search(r'--(\d+)$', url.rstrip('/'))
    if m:
        return f"https://forum.donanimhaber.com/m_{m.group(1)}/printable.htm"
    return url  # eşleşmezse olduğu gibi bırak

async def main():
    url = dh_to_printable(EXTRACT_URL)
    info = await fetch_raw_html(url)
    print(info)

if __name__ == "__main__":
    asyncio.run(main())
