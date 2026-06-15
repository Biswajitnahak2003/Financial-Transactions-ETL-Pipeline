from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text
import pandas as pd
import os
from pathlib import Path
from dotenv import load_dotenv
import numpy as np

load_dotenv()

app = FastAPI(title="Financial Transactions Analytics API")

# DB Config from env or defaults
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "rootpassword")
DB_NAME = os.getenv("DB_NAME", "financial_data")
DB_PORT = os.getenv("DB_PORT", "3307")

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
            NULLIF(LAG(SUM(total_amount)) OVER (ORDER BY DATE_FORMAT(transaction_date, '%Y-%m')), 0) * 100 as growth_pct
        FROM fact_transactions
        GROUP BY month
    ) t;
    """
    try:
        df = pd.read_sql(query, engine)
        # Replace infinite values and NaNs with None so JSON serialization succeeds
        df = df.replace([np.inf, -np.inf], None)
        df = df.where(pd.notnull(df), None)
        import math
        records = []
        for r in df.to_dict(orient="records"):
            new = {}
            for k, v in r.items():
                try:
                    if v is None:
                        new[k] = None
                    elif isinstance(v, float):
                        new[k] = float(v) if math.isfinite(v) else None
                    elif isinstance(v, (int,)):
                        new[k] = int(v)
                    else:
                        # datetimes -> ISO, numpy scalars -> Python native, fall back to str
                        if hasattr(v, "isoformat"):
                            try:
                                new[k] = v.isoformat()
                            except Exception:
                                new[k] = str(v)
                        else:
                            try:
                                # numpy scalar
                                new[k] = v.item()
                            except Exception:
                                new[k] = v
                except Exception:
                    new[k] = None
            records.append(new)
        return records
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
        df = df.replace([np.inf, -np.inf], None)
        df = df.where(pd.notnull(df), None)
        import math
        records = []
        for r in df.to_dict(orient="records"):
            new = {}
            for k, v in r.items():
                try:
                    if v is None:
                        new[k] = None
                    elif isinstance(v, float):
                        new[k] = float(v) if math.isfinite(v) else None
                    elif isinstance(v, (int,)):
                        new[k] = int(v)
                    else:
                        if hasattr(v, "isoformat"):
                            try:
                                new[k] = v.isoformat()
                            except Exception:
                                new[k] = str(v)
                        else:
                            try:
                                new[k] = v.item()
                            except Exception:
                                new[k] = v
                except Exception:
                    new[k] = None
            records.append(new)
        return records
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

ROOT_DIR = Path(__file__).resolve().parents[3]
BAD_RECORDS_PATH = ROOT_DIR / "data" / "processed" / "bad_records.csv"

@app.get("/analytics/metrics")
def get_pipeline_metrics():
    try:
        with engine.connect() as conn:
            total_transactions = conn.execute(text("SELECT COUNT(*) FROM fact_transactions")).scalar()
            total_revenue = conn.execute(text("SELECT COALESCE(SUM(total_amount), 0) FROM fact_transactions")).scalar()
            total_customers = conn.execute(text("SELECT COUNT(*) FROM dim_customers")).scalar()
            total_products = conn.execute(text("SELECT COUNT(*) FROM dim_products")).scalar()
            avg_order_value = conn.execute(text("SELECT COALESCE(AVG(total_amount), 0) FROM fact_transactions")).scalar()
            total_quantity = conn.execute(text("SELECT COALESCE(SUM(quantity), 0) FROM fact_transactions")).scalar()

        bad_count = 0
        if BAD_RECORDS_PATH.exists():
            bad_df = pd.read_csv(BAD_RECORDS_PATH)
            bad_count = len(bad_df)

        total_processed = total_transactions + bad_count
        data_quality_pct = round((total_transactions / total_processed * 100), 2) if total_processed > 0 else 0

        return {
            "total_records_processed": total_processed,
            "valid_records_loaded": total_transactions,
            "invalid_records_rejected": bad_count,
            "data_quality_percentage": data_quality_pct,
            "total_revenue": round(float(total_revenue), 2),
            "total_customers": total_customers,
            "total_products": total_products,
            "average_order_value": round(float(avg_order_value), 2),
            "total_items_sold": int(total_quantity),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health/data-quality")
def get_data_quality():
    if not BAD_RECORDS_PATH.exists():
        return {"error": "Bad records file not found. Run ETL first."}
    
    bad_df = pd.read_csv(BAD_RECORDS_PATH)
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
