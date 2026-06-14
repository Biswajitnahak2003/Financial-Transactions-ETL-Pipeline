# 📊 Financial Transactions Data Pipeline

An end-to-end data engineering pipeline that transforms raw transactional data into actionable business insights. This project demonstrates a complete lifecycle of data: from ingestion and rigorous validation to structured storage and real-time analytics.

## 🚀 Project Overview
The goal of this project is to build a production-ready ETL pipeline that ingests messy financial data, enforces strict business rules, and stores it in a highly optimized Star Schema for fast analytical querying.

### Key Engineering Highlights:
- **Data Quality Gate:** Implemented a row-level validation layer using **Pydantic**, catching 2.2% of invalid records (e.g., negative quantities, invalid prices) and exporting them for auditing.
- **Optimized Storage:** Architected a **MySQL Star Schema** (Fact & Dimension tables), reducing data redundancy and improving query performance for large-scale aggregations.
- **Analytics Engine:** Developed a **FastAPI** backend utilizing advanced SQL (CTEs and Window Functions) to provide real-time business KPIs.
- **Interactive Visualization:** Built a **Streamlit** dashboard to visualize revenue trends and customer lifetime value.
- **DevOps Ready:** Fully containerized the stack using **Docker Compose** for reproducible deployments across any environment.

---

## 🏗️ Architecture
`Raw Data (XLSX)` $\rightarrow$ `Pandas Ingestion` $\rightarrow$ `Pydantic Validation` $\rightarrow$ `MySQL (Star Schema)` $\rightarrow$ `FastAPI` $\rightarrow$ `Streamlit Dashboard`

### Database Design:
- **`dim_customers`**: Stores customer demographics and country.
- **`dim_products`**: Stores product catalogs and descriptions.
- **`fact_transactions`**: Central fact table storing transaction amounts, timestamps, and foreign keys to dimensions.

---

## 🛠️ Tech Stack
- **Language:** Python 3.11
- **Data Processing:** Pandas, Pydantic
- **Database:** MySQL 8.0, SQLAlchemy
- **Backend:** FastAPI, Uvicorn
- **Frontend:** Streamlit, Plotly
- **Infrastructure:** Docker, Docker Compose

---

## 🚦 Getting Started

### Prerequisites
- Docker installed.

### Setup and Run
1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd fin-data-pipeline
   ```

2. **Launch the Infrastructure:**
   ```bash
   docker compose up -d
   ```

3. **Run the ETL Pipeline:**
   ```bash
   # Create virtual environment and install deps
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   
   # Execute the pipeline
   python src/pipeline/etl.py
   ```

4. **Access the Application:**
   - **API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Analytics Dashboard:** [http://localhost:8501](http://localhost:8501)

---

## 📊 Data Quality Report
The pipeline automatically generates a `bad_records.csv` in the `data/processed/` directory. This report includes:
- Row index of the failing record.
- Specific Pydantic validation error (e.g., `Quantity must be greater than 0`).
- The original raw data for debugging.

## 📜 Citation
D. Chen. "Online Retail," UCI Machine Learning Repository, 2015. [Online]. Available: https://doi.org/10.24432/C5BW33.
