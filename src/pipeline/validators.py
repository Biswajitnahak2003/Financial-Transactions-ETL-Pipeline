from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional

class TransactionModel(BaseModel):
    InvoiceNo: str
    StockCode: str
    Description: Optional[str] = None
    Quantity: int = Field(..., gt=0)  # Must be greater than 0
    InvoiceDate: datetime
    UnitPrice: float = Field(..., gt=0) # Must be greater than 0
    CustomerID: Optional[str] = None
    Country: str

    @validator('CustomerID', pre=True)
    def handle_empty_customer(cls, v):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return "GUEST_USER"
        return str(v)

# Note: Since Pydantic validators can't easily access pandas.isna inside the class definition 
# without an import, I'll refine this in the actual ETL script to handle NaNs before Pydantic.
