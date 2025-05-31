from pydantic import BaseModel
from typing import List, Optional

class ReviewItem(BaseModel):
    product_name: str
    review_text: str
    rating: Optional[str] = "N/A" # Default to "N/A" if not found
    sentiment_label: str
    sentiment_score: float

class ScrapeRequest(BaseModel):
    product_url: str

class ScrapeResponse(BaseModel):
    message: str
    data: List[ReviewItem]
    sheet_url: str