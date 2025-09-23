import asyncio, json

from extract import extract_from_google_maps

async def main():
    data = await extract_from_google_maps("izmir", count=1)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
if __name__ == "__main__":
    asyncio.run(main())

