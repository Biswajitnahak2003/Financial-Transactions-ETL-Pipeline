from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Financial Transactions Analytics API")

# DB Config from env or defaults
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "rootpassword")
DB_NAME = os.getenv("DB_NAME", "financial_data")
DB_PORT = "3307" # Matching our docker mapping

engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Financial Data Pipeline API", "status": "online"}

@app.get("/analytics/monthly-revenue")
def get_monthly_revenue():
    query = """
    SELECT 
        month, 
        monthly_revenue,
        prev_month_revenue,
        growth_pct
    FROM (
        SELECT 
            DATE_FORMAT(transaction_date, '%Y-%m') as month, 
            SUM(total_amount) as monthly_revenue,
            LAG(SUM(total_amount)) OVER (ORDER BY DATE_FORMAT(transaction_date, '%Y-%m')) as prev_month_revenue,
            (SUM(total_amount) - LAG(SUM(total_amount)) OVER (ORDER BY DATE_FORMAT(transaction_date, '%Y-%m'))) / 
            LAG(SUM(total_amount)) OVER (ORDER BY DATE_FORMAT(transaction_date, '%Y-%m')) * 100 as growth_pct
        FROM fact_transactions
        GROUP BY month
    ) t;
    """
    try:
        df = pd.read_sql(query, engine)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/top-customers")
def get_top_customers():
    query = """
    WITH CustomerSpend AS (
        SELECT 
            c.customer_id, 
            c.country, 
            SUM(f.total_amount) as total_spent,
            COUNT(f.transaction_id) as total_orders
        FROM dim_customers c
        JOIN fact_transactions f ON c.customer_id = f.customer_id
        GROUP BY 1, 2
    )
    SELECT * FROM CustomerSpend ORDER BY total_spent DESC LIMIT 10;
    """
    try:
        df = pd.read_sql(query, engine)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health/data-quality")
def get_data_quality():
    # Read bad records CSV
    bad_records_path = '/home/biswa/fin-data-pipeline/data/processed/bad_records.csv'
    if not os.path.exists(bad_records_path):
        return {"error": "Bad records file not found. Run ETL first."}
    
    bad_df = pd.read_csv(bad_records_path)
    total_bad = len(bad_df)
    
    # Calculate error distribution
    error_dist = bad_df['error'].value_counts().to_dict() if 'error' in bad_df.columns else {}
    
    return {
        "total_bad_records": total_bad,
        "error_distribution": error_dist,
        "status": "Report Generated"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
