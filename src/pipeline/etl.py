import pandas as pd
from pydantic import ValidationError
from sqlalchemy import create_engine, text
from pathlib import Path
import os

from validators import TransactionModel

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
    project_root = Path(__file__).resolve().parents[2]
    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    excel_file = raw_dir / "Online Retail.xlsx"
    csv_file = raw_dir / "online_retail.csv"

    if excel_file.exists():
        input_file = excel_file
        print(f"Reading Excel data from {input_file}...")
        df = pd.read_excel(input_file)
    elif csv_file.exists():
        input_file = csv_file
        print(f"Reading CSV data from {input_file}...")
        df = pd.read_csv(input_file)
    else:
        raise FileNotFoundError(
            f"Could not find input data file in {raw_dir}. "
            "Expected one of: 'Online Retail.xlsx', 'online_retail.csv'."
        )

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
    
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3307")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "rootpassword")
    DB_NAME = os.getenv("DB_NAME", "financial_data")
    
    engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    
    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        conn.execute(text("TRUNCATE TABLE fact_transactions;"))
        conn.execute(text("TRUNCATE TABLE dim_customers;"))
        conn.execute(text("TRUNCATE TABLE dim_products;"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
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
    bad_path = processed_dir / 'bad_records.csv'
    bad_df.to_csv(bad_path, index=False)
    print(f"Bad records saved to {bad_path}")

if __name__ == "__main__":
    run_etl()
