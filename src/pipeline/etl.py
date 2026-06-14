import pandas as pd
from pydantic import BaseModel, Field, validator, ValidationError
from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy import create_engine, text
import os

class TransactionModel(BaseModel):
    InvoiceNo: str
    StockCode: str
    Description: Optional[str] = None
    Quantity: int = Field(..., gt=0)
    InvoiceDate: datetime
    UnitPrice: float = Field(..., gt=0)
    CustomerID: str
    Country: str

def validate_row(row):
    try:
        data = row.to_dict()
        data = {k: (None if pd.isna(v) else v) for k, v in data.items()}
        if data['CustomerID'] is None:
            data['CustomerID'] = 'GUEST_USER'
        return TransactionModel(**data), None
    except ValidationError as e:
        return None, str(e)

def run_etl():
    print("Starting ETL Process...")
    # Read directly from Excel to avoid separate conversion script
    input_file = '/home/biswa/fin-data-pipeline/data/raw/Online Retail.xlsx'
    print(f"Reading data from {input_file}...")
    df = pd.read_excel(input_file)
    
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
    df['StockCode'] = df['StockCode'].astype(str).str.upper()
    df['CustomerID'] = df['CustomerID'].astype(str).str.upper()
    
    good_records = []
    bad_records = []
    
    print(f"Validating {len(df)} records...")
    for index, row in df.iterrows():
        valid_rec, error = validate_row(row)
        if valid_rec:
            good_records.append(valid_rec.model_dump())
        else:
            bad_records.append({"row": index, "error": error, "data": row.to_dict()})
            
    print(f"Validation Complete: {len(good_records)} good, {len(bad_records)} bad.")
    
    clean_df = pd.DataFrame(good_records)
    clean_df['total_amount'] = clean_df['Quantity'] * clean_df['UnitPrice']
    
    engine = create_engine('mysql+pymysql://root:rootpassword@localhost:3307/financial_data')
    
    with engine.connect() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        conn.execute(text("TRUNCATE TABLE fact_transactions;"))
        conn.execute(text("TRUNCATE TABLE dim_customers;"))
        conn.execute(text("TRUNCATE TABLE dim_products;"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        conn.commit()
    print("Tables truncated for fresh load.")
    
    customers = clean_df[['CustomerID', 'Country']].drop_duplicates('CustomerID')
    customers = customers.rename(columns={'CustomerID': 'customer_id', 'Country': 'country'})
    customers.to_sql('dim_customers', engine, if_exists='append', index=False)
    print("Loaded dim_customers.")
    
    products = clean_df[['StockCode', 'Description']].drop_duplicates('StockCode')
    products = products.rename(columns={'StockCode': 'stock_code', 'Description': 'description'})
    products.to_sql('dim_products', engine, if_exists='append', index=False)
    print("Loaded dim_products.")
    
    clean_df['transaction_id'] = [f"TXN_{i}" for i in range(len(clean_df))]
    fact_mapping = {
        'transaction_id': 'transaction_id',
        'InvoiceNo': 'invoice_no',
        'CustomerID': 'customer_id',
        'StockCode': 'stock_code',
        'Quantity': 'quantity',
        'UnitPrice': 'unit_price',
        'total_amount': 'total_amount',
        'InvoiceDate': 'transaction_date'
    }
    fact_df = clean_df[list(fact_mapping.keys())].rename(columns=fact_mapping)
    fact_df.to_sql('fact_transactions', engine, if_exists='append', index=False)
    print("Loaded fact_transactions.")
    
    bad_df = pd.DataFrame(bad_records)
    bad_df.to_csv('/home/biswa/fin-data-pipeline/data/processed/bad_records.csv', index=False)
    print("Bad records saved to data/processed/bad_records.csv")

if __name__ == "__main__":
    run_etl()
