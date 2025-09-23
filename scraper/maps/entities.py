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
         "type": "text"}
    ],
}