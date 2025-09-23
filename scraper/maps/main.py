import asyncio, json

from extract import extract_with_css
from models import EXTRACT_URL

async def main():
    data = await extract_with_css(EXTRACT_URL)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
if __name__ == "__main__":
    asyncio.run(main())

