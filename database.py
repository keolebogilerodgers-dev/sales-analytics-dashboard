"""
Database Module for Sales Analytics Dashboard
Creates and populates SQLite database with realistic sales data.
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

class SalesDatabase:
    def __init__(self, db_path='sales.db'):
        self.db_path = db_path
        self.connection = None
        
    def connect(self):
        """Establish connection to SQLite database."""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row  # Enable dictionary-like access
        return self.connection
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
    
    def create_tables(self):
        """Create all necessary tables with proper schema."""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Drop existing tables if they exist (for clean setup)
        cursor.execute("DROP TABLE IF EXISTS sales_transactions")
        cursor.execute("DROP TABLE IF EXISTS products")
        cursor.execute("DROP TABLE IF EXISTS customers")
        cursor.execute("DROP TABLE IF EXISTS regions")
        
        # Create products table
        cursor.execute("""
        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            category TEXT NOT NULL,
            base_price REAL NOT NULL,
            cost_price REAL NOT NULL,
            supplier TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create regions table
        cursor.execute("""
        CREATE TABLE regions (
            region_id INTEGER PRIMARY KEY AUTOINCREMENT,
            region_name TEXT NOT NULL UNIQUE,
            manager TEXT,
            target_sales REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create customers table
        cursor.execute("""
        CREATE TABLE customers (
            customer_id TEXT PRIMARY KEY,
            customer_name TEXT,
            email TEXT,
            region_id INTEGER,
            customer_segment TEXT,
            first_purchase_date DATE,
            total_purchases REAL DEFAULT 0,
            FOREIGN KEY (region_id) REFERENCES regions (region_id)
        )
        """)
        
        # Create main sales transactions table
        cursor.execute("""
        CREATE TABLE sales_transactions (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT NOT NULL UNIQUE,
            customer_id TEXT,
            product_id INTEGER,
            region_id INTEGER,
            sales_rep TEXT,
            transaction_date DATE NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            unit_price REAL NOT NULL CHECK(unit_price > 0),
            total_sales REAL NOT NULL CHECK(total_sales > 0),
            cost_price REAL NOT NULL,
            total_cost REAL NOT NULL,
            profit REAL NOT NULL,
            margin_percent REAL NOT NULL,
            payment_method TEXT,
            shipping_status TEXT,
            day_of_week TEXT,
            month TEXT,
            quarter TEXT,
            year INTEGER,
            is_weekend BOOLEAN,
            seasonal_factor REAL DEFAULT 1.0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers (customer_id),
            FOREIGN KEY (product_id) REFERENCES products (product_id),
            FOREIGN KEY (region_id) REFERENCES regions (region_id)
        )
        """)
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX idx_transaction_date ON sales_transactions(transaction_date)")
        cursor.execute("CREATE INDEX idx_product_id ON sales_transactions(product_id)")
        cursor.execute("CREATE INDEX idx_region_id ON sales_transactions(region_id)")
        cursor.execute("CREATE INDEX idx_customer_id ON sales_transactions(customer_id)")
        
        # Create views for common queries
        cursor.execute("""
        CREATE VIEW daily_sales_summary AS
        SELECT 
            transaction_date,
            COUNT(*) as transaction_count,
            SUM(total_sales) as daily_sales,
            SUM(profit) as daily_profit,
            AVG(margin_percent) as avg_margin
        FROM sales_transactions
        GROUP BY transaction_date
        ORDER BY transaction_date DESC
        """)
        
        cursor.execute("""
        CREATE VIEW top_products_view AS
        SELECT 
            p.product_name,
            p.category,
            COUNT(st.transaction_id) as sales_count,
            SUM(st.total_sales) as total_revenue,
            SUM(st.profit) as total_profit,
            AVG(st.margin_percent) as avg_margin
        FROM sales_transactions st
        JOIN products p ON st.product_id = p.product_id
        GROUP BY p.product_name, p.category
        ORDER BY total_revenue DESC
        """)
        
        conn.commit()
        print("✅ Database tables and views created successfully!")
        
    def insert_sample_data(self):
        """Insert realistic sample data into all tables."""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Insert products
        products = [
            ('Laptop Pro X1', 'Electronics', 899.99, 650.00, 'TechSuppliers Inc'),
            ('Smartphone Alpha 12', 'Electronics', 699.99, 500.00, 'MobileTech Co'),
            ('Tablet Plus', 'Electronics', 399.99, 280.00, 'TechSuppliers Inc'),
            ('27" Gaming Monitor', 'Computers', 249.99, 180.00, 'DisplayMasters'),
            ('Wireless Headphones', 'Accessories', 149.99, 85.00, 'AudioTech'),
            ('Mechanical Keyboard', 'Accessories', 79.99, 45.00, 'InputDevices Ltd'),
            ('Gaming Mouse', 'Accessories', 39.99, 22.00, 'InputDevices Ltd'),
            ('4K Webcam', 'Accessories', 89.99, 55.00, 'VideoTech Corp'),
            ('Laptop Stand', 'Accessories', 34.99, 20.00, 'ErgoWorks'),
            ('USB-C Hub', 'Accessories', 39.99, 25.00, 'Connectivity Solutions')
        ]
        
        cursor.executemany(
            "INSERT INTO products (product_name, category, base_price, cost_price, supplier) VALUES (?, ?, ?, ?, ?)",
            products
        )
        
        # Insert regions
        regions = [
            ('North America', 'Sarah Johnson', 250000),
            ('Europe', 'Michael Chen', 200000),
            ('Asia Pacific', 'Priya Sharma', 180000),
            ('Latin America', 'Carlos Rodriguez', 120000),
            ('Middle East', 'Ahmed Al-Farsi', 80000)
        ]
        
        cursor.executemany(
            "INSERT INTO regions (region_name, manager, target_sales) VALUES (?, ?, ?)",
            regions
        )
        
        # Insert sample customers
        customers = []
        regions_list = ['North America', 'Europe', 'Asia Pacific', 'Latin America', 'Middle East']
        
        for i in range(1, 101):
            region_idx = i % 5
            customers.append((
                f"CUST{10000 + i}",
                f"Customer {i}",
                f"customer{i}@example.com",
                region_idx + 1,
                'Premium' if i % 4 == 0 else 'Standard',
                f"2024-{str((i % 12) + 1).zfill(2)}-{str((i % 28) + 1).zfill(2)}"
            ))
        
        cursor.executemany(
            """INSERT INTO customers 
               (customer_id, customer_name, email, region_id, customer_segment, first_purchase_date) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            customers
        )
        
        # Generate sales transactions
        np.random.seed(42)
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 6, 30)
        date_range = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]
        
        transactions = []
        order_counter = 1000
        
        # Get product and region IDs for foreign key references
        cursor.execute("SELECT product_id, base_price, cost_price FROM products")
        product_data = cursor.fetchall()
        
        cursor.execute("SELECT region_id FROM regions")
        region_ids = [row[0] for row in cursor.fetchall()]
        
        for date in date_range:
            # Daily transaction volume with seasonality
            day_of_week = date.weekday()
            is_weekend = day_of_week >= 5
            month = date.month
            
            # Seasonal factors
            seasonal_factor = 1.0
            if month in [11, 12]:  # Holiday season
                seasonal_factor = 1.5
            elif month in [6, 7]:  # Summer
                seasonal_factor = 0.8
            
            # Weekend boost
            daily_factor = 1.4 if is_weekend else 1.0
            base_transactions = 25
            
            # Adjust for seasonality and day of week
            daily_transactions = int(base_transactions * seasonal_factor * daily_factor * np.random.uniform(0.8, 1.2))
            daily_transactions = max(10, min(daily_transactions, 60))
            
            for _ in range(daily_transactions):
                order_counter += 1
                product = product_data[np.random.randint(0, len(product_data))]
                product_id, base_price, cost_price = product
                
                region_id = np.random.choice(region_ids)
                customer_id = f"CUST{10000 + np.random.randint(1, 101)}"
                
                # Sales rep based on region
                sales_reps = ['Alex Johnson', 'Maria Garcia', 'David Chen', 'Sarah Williams', 'James Brown']
                sales_rep = sales_reps[region_id - 1]
                
                # Dynamic pricing
                region_multiplier = {
                    1: 1.0,  # North America
                    2: 1.1,  # Europe
                    3: 0.95, # Asia Pacific
                    4: 0.85, # Latin America
                    5: 1.2   # Middle East
                }
                
                price_variation = np.random.uniform(0.92, 1.08)
                unit_price = base_price * region_multiplier[region_id] * price_variation
                
                # Quantity with realistic distribution
                quantity_options = [1, 1, 1, 2, 2, 3, 1, 1, 2, 1]
                quantity = np.random.choice(quantity_options)
                
                # Calculate financials
                total_sales = unit_price * quantity * seasonal_factor * (1.4 if is_weekend else 1.0)
                total_cost = cost_price * quantity
                profit = total_sales - total_cost
                margin_percent = (profit / total_sales * 100) if total_sales > 0 else 0
                
                # Payment methods
                payment_methods = ['Credit Card', 'PayPal', 'Bank Transfer', 'Cash']
                payment_method = np.random.choice(payment_methods, p=[0.6, 0.2, 0.15, 0.05])
                
                # Shipping status
                shipping_options = ['Delivered', 'Shipped', 'Processing', 'Pending']
                shipping_probs = [0.7, 0.2, 0.08, 0.02]
                shipping_status = np.random.choice(shipping_options, p=shipping_probs)
                
                transactions.append((
                    f"ORD{date.strftime('%Y%m%d')}{order_counter}",
                    customer_id,
                    product_id,
                    region_id,
                    sales_rep,
                    date.strftime('%Y-%m-%d'),
                    quantity,
                    round(unit_price, 2),
                    round(total_sales, 2),
                    cost_price,
                    round(total_cost, 2),
                    round(profit, 2),
                    round(margin_percent, 2),
                    payment_method,
                    shipping_status,
                    date.strftime('%A'),
                    date.strftime('%B'),
                    f"Q{(date.month-1)//3 + 1}",
                    date.year,
                    1 if is_weekend else 0,
                    seasonal_factor,
                    'Sample transaction for demo'
                ))
        
        # Insert in batches for performance
        batch_size = 1000
        for i in range(0, len(transactions), batch_size):
            batch = transactions[i:i + batch_size]
            cursor.executemany("""
                INSERT INTO sales_transactions (
                    order_id, customer_id, product_id, region_id, sales_rep,
                    transaction_date, quantity, unit_price, total_sales, cost_price,
                    total_cost, profit, margin_percent, payment_method, shipping_status,
                    day_of_week, month, quarter, year, is_weekend, seasonal_factor, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, batch)
            conn.commit()
            print(f"   Inserted batch {i//batch_size + 1}/{(len(transactions)//batch_size)+1}")
        
        # Update customer totals
        cursor.execute("""
            UPDATE customers 
            SET total_purchases = (
                SELECT COALESCE(SUM(total_sales), 0) 
                FROM sales_transactions st 
                WHERE st.customer_id = customers.customer_id
            )
        """)
        
        conn.commit()
        print(f"✅ Database populated with {len(transactions):,} sales transactions!")
        
        # Return some stats
        cursor.execute("SELECT COUNT(*) FROM sales_transactions")
        transaction_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(total_sales) FROM sales_transactions")
        total_sales = cursor.fetchone()[0]
        
        return {
            "transactions": transaction_count,
            "total_sales": total_sales,
            "date_range": f"{start_date.date()} to {end_date.date()}"
        }
    
    def get_database_stats(self):
        """Get statistics about the database."""
        conn = self.connect()
        cursor = conn.cursor()
        
        stats = {}
        
        # Table counts
        tables = ['products', 'regions', 'customers', 'sales_transactions']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[table] = cursor.fetchone()[0]
        
        # Date range
        cursor.execute("SELECT MIN(transaction_date), MAX(transaction_date) FROM sales_transactions")
        min_date, max_date = cursor.fetchone()
        stats['date_range'] = f"{min_date} to {max_date}"
        
        # Financial totals
        cursor.execute("SELECT SUM(total_sales), SUM(profit), AVG(margin_percent) FROM sales_transactions")
        total_sales, total_profit, avg_margin = cursor.fetchone()
        stats['total_sales'] = total_sales
        stats['total_profit'] = total_profit
        stats['avg_margin'] = avg_margin
        
        return stats
    
    def run_custom_query(self, query, params=None):
        """Execute a custom SQL query and return results."""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Get column names
            columns = [description[0] for description in cursor.description] if cursor.description else []
            
            # Fetch results
            results = cursor.fetchall()
            
            # Convert to list of dictionaries
            if columns and results:
                data = [dict(zip(columns, row)) for row in results]
            else:
                data = []
            
            return {
                "success": True,
                "columns": columns,
                "data": data,
                "row_count": len(data)
            }
            
        except sqlite3.Error as e:
            return {
                "success": False,
                "error": str(e),
                "columns": [],
                "data": [],
                "row_count": 0
            }
    
    def export_to_csv(self, table_name, file_path):
        """Export a table to CSV file."""
        conn = self.connect()
        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql_query(query, conn)
        df.to_csv(file_path, index=False)
        return f"Exported {len(df)} rows to {file_path}"

# Initialize database when this module is run directly
if __name__ == "__main__":
    print("🚀 Initializing Sales Database...")
    db = SalesDatabase()
    db.create_tables()
    stats = db.insert_sample_data()
    db.close()
    
    print("\n📊 Database Initialization Complete!")
    print(f"   • Transactions: {stats['transactions']:,}")
    print(f"   • Total Sales: ${stats['total_sales']:,.2f}")
    print(f"   • Date Range: {stats['date_range']}")
    print("\n✅ Database is ready for the Sales Analytics Dashboard!")
