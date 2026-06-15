import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Financial Data Dashboard", layout="wide")

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.title("📊 Financial Transactions Dashboard")
st.markdown("Real-time analytics from the Data Pipeline")

# Sidebar for navigation
menu = ["Pipeline Metrics", "Revenue Trends", "Customer Insights", "Data Quality"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Pipeline Metrics":
    st.subheader("📊 Pipeline Metrics Overview")
    try:
        res = requests.get(f"{API_BASE_URL}/analytics/metrics")
        data = res.json()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Records Processed", f"{data.get('total_records_processed', 0):,}")
        col2.metric("Valid Records Loaded", f"{data.get('valid_records_loaded', 0):,}")
        col3.metric("Invalid Records Rejected", f"{data.get('invalid_records_rejected', 0):,}")
        col4.metric("Data Quality", f"{data.get('data_quality_percentage', 0)}%")

        col5, col6, col7, col8 = st.columns(4)
        col5.metric("Total Revenue", f"${data.get('total_revenue', 0):,.2f}")
        col6.metric("Total Customers", f"{data.get('total_customers', 0):,}")
        col7.metric("Total Products", f"{data.get('total_products', 0):,}")
        col8.metric("Avg Order Value", f"${data.get('average_order_value', 0):,.2f}")

        st.metric("Total Items Sold", f"{data.get('total_items_sold', 0):,}")
    except Exception as e:
        st.error(f"API Error: {e}")

elif choice == "Revenue Trends":
    st.subheader("📈 Monthly Revenue Growth")
    try:
        res = requests.get(f"{API_BASE_URL}/analytics/monthly-revenue")
        data = res.json()
        # Ensure data is a list of records for DataFrame construction
        if isinstance(data, dict):
            data = [data]
        df = pd.DataFrame(data)
        
        if not df.empty:
            fig = px.line(df, x="month", y="monthly_revenue", title="Monthly Revenue over Time")
            st.plotly_chart(fig, use_container_width=True)
            st.table(df)
        else:
            st.write("No data available.")
    except Exception as e:
        st.error(f"API Error: {e}")

elif choice == "Customer Insights":
    st.subheader("👥 Top Customers by Lifetime Value")
    try:
        res = requests.get(f"{API_BASE_URL}/analytics/top-customers")
        data = res.json()
        if isinstance(data, dict):
            data = [data]
        df = pd.DataFrame(data)
        
        if not df.empty:
            fig = px.bar(df, x="customer_id", y="total_spent", color="country", title="Top 10 Customers")
            st.plotly_chart(fig, use_container_width=True)
            st.table(df)
        else:
            st.write("No data available.")
    except Exception as e:
        st.error(f"API Error: {e}")

elif choice == "Data Quality":
    st.subheader("🛠️ Pipeline Data Quality Report")
    try:
        res = requests.get(f"{API_BASE_URL}/health/data-quality")
        data = res.json()
        
        st.metric("Total Bad Records", data.get("total_bad_records", 0))
        
        if "error_distribution" in data:
            st.write("Error Distribution:")
            dist_df = pd.DataFrame(list(data["error_distribution"].items()), columns=["Error", "Count"])
            st.table(dist_df)
    except Exception as e:
        st.error(f"API Error: {e}")
