-- Create Database
CREATE DATABASE IF NOT EXISTS financial_data;
USE financial_data;

-- Dimension: Customers
CREATE TABLE IF NOT EXISTS dim_customers (
    customer_id VARCHAR(20) PRIMARY KEY,
    country VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimension: Products
CREATE TABLE IF NOT EXISTS dim_products (
    stock_code VARCHAR(20) PRIMARY KEY,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fact: Transactions
CREATE TABLE IF NOT EXISTS fact_transactions (
    transaction_id VARCHAR(50) PRIMARY KEY,
    invoice_no VARCHAR(20) NOT NULL,
    customer_id VARCHAR(20),
    stock_code VARCHAR(20),
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    transaction_date DATETIME NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES dim_customers(customer_id),
    FOREIGN KEY (stock_code) REFERENCES dim_products(stock_code)
);

-- Indexes for performance
CREATE INDEX idx_transaction_date ON fact_transactions(transaction_date);
CREATE INDEX idx_customer_id ON fact_transactions(customer_id);
