from datetime import date
from pydantic import BaseModel, ConfigDict, Field

class SaleCreate(BaseModel):
    order_id: str = Field(min_length=1, max_length=80)
    order_date: date
    customer: str = "Unknown"
    product: str
    category: str = "Uncategorized"
    region: str = "Unknown"
    quantity: int = Field(ge=1)
    unit_price: float = Field(ge=0)
    unit_cost: float = Field(ge=0)

class SaleOut(SaleCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)

class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)

class ChatResponse(BaseModel):
    answer: str
    source: str
    data: dict | list | None = None
