import pandas as pd
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional


class TransactionModel(BaseModel):
    InvoiceNo: str
    StockCode: str
    Description: Optional[str] = None
    Quantity: int = Field(..., gt=0)
    InvoiceDate: datetime
    UnitPrice: float = Field(..., gt=0)
    CustomerID: Optional[str] = None
    Country: str

    @field_validator('InvoiceNo', 'StockCode', 'Country', 'Description', mode='before')
    def coerce_string(cls, v):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return None
        return str(v).strip()

    @field_validator('CustomerID', mode='before')
    def handle_empty_customer(cls, v):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return "GUEST_USER"
        if isinstance(v, str) and v.strip().lower() in {'nan', ''}:
            return "GUEST_USER"
        return str(v).strip()
