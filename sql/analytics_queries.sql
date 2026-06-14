-- 1. Monthly Revenue Trends (Window Function)
-- Shows total revenue and the percentage growth from previous month
SELECT 
    month, 
    monthly_revenue,
    LAG(monthly_revenue) OVER (ORDER BY month) as prev_month_revenue,
    (monthly_revenue - LAG(monthly_revenue) OVER (ORDER BY month)) / LAG(monthly_revenue) OVER (ORDER BY month) * 100 as growth_pct
FROM (
    SELECT 
        DATE_FORMAT(transaction_date, '%Y-%m') as month, 
        SUM(total_amount) as monthly_revenue
    FROM fact_transactions
    GROUP BY 1
) t;

-- 2. Customer Lifetime Value (CTE)
-- Top 10 customers by total spend
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

-- 3. Top 10 Products by Revenue
SELECT 
    p.description, 
    SUM(f.total_amount) as revenue
FROM dim_products p
JOIN fact_transactions f ON p.stock_code = f.stock_code
GROUP BY 1
ORDER BY revenue DESC
LIMIT 10;

-- 4. Data Quality Summary
-- We'll handle this in Python, but here's a query for missing values in the DB
SELECT 
    'dim_customers' as table_name, COUNT(*) as total_rows, SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) as nulls 
    FROM dim_customers
UNION ALL
SELECT 
    'dim_products' as table_name, COUNT(*) as total_rows, SUM(CASE WHEN stock_code IS NULL THEN 1 ELSE 0 END) as nulls 
    FROM dim_products
UNION ALL
SELECT 
    'fact_transactions' as table_name, COUNT(*) as total_rows, SUM(CASE WHEN transaction_id IS NULL THEN 1 ELSE 0 END) as nulls 
    FROM fact_transactions;
