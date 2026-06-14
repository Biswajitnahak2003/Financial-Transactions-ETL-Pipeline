import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Financial Data Dashboard", layout="wide")

API_BASE_URL = "http://localhost:8000"

st.title("📊 Financial Transactions Dashboard")
st.markdown("Real-time analytics from the Data Pipeline")

# Sidebar for navigation
menu = ["Revenue Trends", "Customer Insights", "Data Quality"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Revenue Trends":
    st.subheader("📈 Monthly Revenue Growth")
    try:
        res = requests.get(f"{API_BASE_URL}/analytics/monthly-revenue")
        data = res.json()
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
