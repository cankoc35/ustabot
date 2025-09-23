from typing import Optional, List
from pydantic import BaseModel

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
        "[role='feed'] [role='article'][data-result-index], "  
        "[role='feed'] [data-result-index], "                   
        "[role='feed'] .Nv2PK"                                  
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

CITIES = {
    "izmir": "https://www.google.com/maps/search/izmir+en+iyi+oto+tamirciler",
    "İzmir-Bornova": "https://www.google.com/maps/search/izmir+bornova+en+iyi+oto+tamirciler",
    "İzmir-Buca": "https://www.google.com/maps/search/izmir+buca+en+iyi+oto+tamirciler",
    "İzmir-Konak": "https://www.google.com/maps/search/izmir+konak+en+iyi+oto+tamirciler",
    "İzmir-Karşıyaka": "https://www.google.com/maps/search/izmir+karşıyaka+en+iyi+oto+tamirciler",
    "İzmir-Gaziemir": "https://www.google.com/maps/search/izmir+gaziemir+en+iyi+oto+tamirciler",
    "İzmir-Çiğli": "https://www.google.com/maps/search/izmir+çiğli+en+iyi+oto+tamirciler",
    "İzmir-Kemalpaşa": "https://www.google.com/maps/search/izmir+kemalpaşa+en+iyi+oto+tamirciler",
    "İzmir-Menemen": "https://www.google.com/maps/search/izmir+menemen+en+iyi+oto+tamirciler",
    "İzmir-Aliağa": "https://www.google.com/maps/search/izmir+aliağa+en+iyi+oto+tamirciler",
    "İzmir-Torbalı": "https://www.google.com/maps/search/izmir+torbalı+en+iyi+oto+tamirciler",
    "İzmir-Menderes": "https://www.google.com/maps/search/izmir+menderes+en+iyi+oto+tamirciler",
    "İzmir-Seferihisar": "https://www.google.com/maps/search/izmir+seferihisar+en+iyi+oto+tamirciler",
    "İzmir-Bayraklı": "https://www.google.com/maps/search/izmir+bayraklı+en+iyi+oto+tamirciler",
    "İzmir-Urla": "https://www.google.com/maps/search/izmir+urla+en+iyi+oto+tamirciler",    
    "İstanbul": "https://www.google.com/maps/search/istanbul+en+iyi+oto+tamirciler",
    "İstanbul-Avcılar": "https://www.google.com/maps/search/istanbul+avcılar+en+iyi+oto+tamirciler",
    "İstanbul-Bahçelievler": "https://www.google.com/maps/search/istanbul+bahçelievler+en+iyi+oto+tamirciler",
    "İstanbul-Bakırköy": "https://www.google.com/maps/search/istanbul+bakırköy+en+iyi+oto+tamirciler",
    "İstanbul-Beylikdüzü": "https://www.google.com/maps/search/istanbul+beylikdüzü+en+iyi+oto+tamirciler",
    "İstanbul-Beykoz": "https://www.google.com/maps/search/istanbul+beykoz+en+iyi+oto+tamirciler",
    "İstanbul-Beyoğlu": "https://www.google.com/maps/search/istanbul+beyoğlu+en+iyi+oto+tamirciler",
    "İstanbul-Çekmeköy": "https://www.google.com/maps/search/istanbul+çekmeköy+en+iyi+oto+tamirciler",
    "İstanbul-Esenler": "https://www.google.com/maps/search/istanbul+esenler+en+iyi+oto+tamirciler",
    "İstanbul-Esenyurt": "https://www.google.com/maps/search/istanbul+esenyurt+en+iyi+oto+tamirciler",
    "İstanbul-Gaziosmanpaşa": "https://www.google.com/maps/search/istanbul+gaziosmanpaşa+en+iyi+oto+tamirciler",
    "İstanbul-Kadıköy": "https://www.google.com/maps/search/istanbul+kadıköy+en+iyi+oto+tamirciler",
    "İstanbul-Kartal": "https://www.google.com/maps/search/istanbul+kartal+en+iyi+oto+tamirciler",
    "İstanbul-Küçükçekmece": "https://www.google.com/maps/search/istanbul+küçükçekmece+en+iyi+oto+tamirciler",
    "İstanbul-Maltepe": "https://www.google.com/maps/search/istanbul+maltepe+en+iyi+oto+tamirciler",
    "İstanbul-Pendik": "https://www.google.com/maps/search/istanbul+pendik+en+iyi+oto+tamirciler",
    "İstanbul-Sancaktepe": "https://www.google.com/maps/search/istanbul+sancaktepe+en+iyi+oto+tamirciler",
    "İstanbul-Sarıyer": "https://www.google.com/maps/search/istanbul+sarıyer+en+iyi+oto+tamirciler",
    "İstanbul-Silivri": "https://www.google.com/maps/search/istanbul+silivri+en+iyi+oto+tamirciler",
    "İstanbul-Sultanbeyli": "https://www.google.com/maps/search/istanbul+sultanbeyli+en+iyi+oto+tamirciler",
    "İstanbul-Tuzla": "https://www.google.com/maps/search/istanbul+tuzla+en+iyi+oto+tamirciler",
    "İstanbul-Ümraniye": "https://www.google.com/maps/search/istanbul+ümraniye+en+iyi+oto+tamirciler",
    "İstanbul-Üsküdar": "https://www.google.com/maps/search/istanbul+üsküdar+en+iyi+oto+tamirciler",
    "İstanbul-Zeytinburnu": "https://www.google.com/maps/search/istanbul+zeytinburnu+en+iyi+oto+tamirciler",    
    "İstanbul-Başakşehir": "https://www.google.com/maps/search/istanbul+başakşehir+en+iyi+oto+tamirciler",
    "İstanbul-Çatalca": "https://www.google.com/maps/search/istanbul+çatalca+en+iyi+oto+tamirciler",
    "Ankara": "https://www.google.com/maps/search/ankara+en+iyi+oto+tamirciler",
    "Ankara-Çankaya": "https://www.google.com/maps/search/ankara+çankaya+en+iyi+oto+tamirciler",
    "Ankara-Keçiören": "https://www.google.com/maps/search/ankara+keçiören+en+iyi+oto+tamirciler",
    "Ankara-Yenimahalle": "https://www.google.com/maps/search/ankara+yenimahalle+en+iyi+oto+tamirciler",
    "Ankara-Sincan": "https://www.google.com/maps/search/ankara+sincan+en+iyi+oto+tamirciler",
    "Ankara-Etimesgut": "https://www.google.com/maps/search/ankara+etimesgut+en+iyi+oto+tamirciler",
    "Ankara-Mamak": "https://www.google.com/maps/search/ankara+mamak+en+iyi+oto+tamirciler",
    "Ankara-Altındağ": "https://www.google.com/maps/search/ankara+altındağ+en+iyi+oto+tamirciler",
    "Ankara-Kazan": "https://www.google.com/maps/search/ankara+kazan+en+iyi+oto+tamirciler",
    "Ankara-Polatlı": "https://www.google.com/maps/search/ankara+polatlı+en+iyi+oto+tamirciler",
    "Ankara-Gölbaşı": "https://www.google.com/maps/search/ankara+gölbaşı+en+iyi+oto+tamirciler",
    "Ankara-Çubuk": "https://www.google.com/maps/search/ankara+çubuk+en+iyi+oto+tamirciler",
    "Ankara-Kızılcahamam": "https://www.google.com/maps/search/ankara+kızılcahamam+en+iyi+oto+tamirciler",
    "Ankara-Ayaş": "https://www.google.com/maps/search/ankara+ayaş+en+iyi+oto+tamirciler",
}