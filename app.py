"""
Sales Analytics Dashboard with SQL Database Integration
Built by: Keolebogile Rodgers
Demonstrating: Python, SQL, Data Visualization, Web Development
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import sqlite3
from database import SalesDatabase

# ==================== PAGE CONFIGURATION ====================
st.set_page_config(
    page_title="SQL Sales Dashboard | Portfolio Project",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/keolebogilerodgers-dev',
        'About': '### Portfolio Project: SQL Sales Dashboard\n'
                 'Demonstrating SQL Database Integration + Data Science Skills'
    }
)

# ==================== CUSTOM CSS ====================
st.markdown("""
<style>
    .sql-badge {
        background: linear-gradient(90deg, #1E3A8A, #3B82F6);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        margin: 2px;
    }
    .database-card {
        background: #f8f9fa;
        border-left: 4px solid #0d6efd;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ==================== DATABASE INITIALIZATION ====================
@st.cache_resource
def init_database():
    """Initialize and cache database connection."""
    db = SalesDatabase()
    return db

# Initialize database
db = init_database()

# ==================== SIDEBAR - DATABASE CONTROLS ====================
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/1946/1946429.png", width=80)
st.sidebar.title("🗄️ Database Controls")
st.sidebar.markdown("---")

# Database info
with st.sidebar.expander("📊 Database Info", expanded=True):
    stats = db.get_database_stats()
    st.markdown(f"""
    **Sales Database:**
    - <span class='sql-badge'>SQLite</span>
    - **Transactions:** {stats['sales_transactions']:,}
    - **Customers:** {stats['customers']:,}
    - **Products:** {stats['products']:,}
    - **Total Sales:** ${stats['total_sales']:,.0f}
    - **Date Range:** {stats['date_range']}
    """, unsafe_allow_html=True)

# SQL Query Tester
st.sidebar.subheader("🔍 SQL Query Tester")
sample_queries = {
    "Daily Sales": "SELECT * FROM daily_sales_summary LIMIT 10",
    "Top Products": "SELECT * FROM top_products_view LIMIT 10",
    "Customer Stats": """
        SELECT 
            c.customer_segment,
            COUNT(*) as customer_count,
            SUM(c.total_purchases) as total_spent,
            AVG(c.total_purchases) as avg_spent
        FROM customers c
        GROUP BY c.customer_segment
    """,
    "Regional Performance": """
        SELECT 
            r.region_name,
            COUNT(st.transaction_id) as transaction_count,
            SUM(st.total_sales) as total_sales,
            SUM(st.profit) as total_profit,
            AVG(st.margin_percent) as avg_margin
        FROM sales_transactions st
        JOIN regions r ON st.region_id = r.region_id
        GROUP BY r.region_name
        ORDER BY total_sales DESC
    """
}

selected_query = st.sidebar.selectbox("Sample Queries:", list(sample_queries.keys()))
if st.sidebar.button("Run Query"):
    with st.spinner("Executing SQL query..."):
        query = sample_queries[selected_query]
        result = db.run_custom_query(query)
        
        if result["success"]:
            st.sidebar.success(f"✅ Query returned {result['row_count']} rows")
            if result["data"]:
                df_result = pd.DataFrame(result["data"])
                st.sidebar.dataframe(df_result.head(), use_container_width=True)
        else:
            st.sidebar.error(f"Query failed: {result['error']}")

# ==================== DATA LOADING FUNCTIONS ====================
@st.cache_data(ttl=300, show_spinner="Loading data from SQL database...")
def load_sales_data(date_filter=None, product_filter=None, region_filter=None):
    """Load sales data from SQL database with optional filters."""
    
    # Build WHERE clause based on filters
    where_clauses = []
    params = []
    
    if date_filter:
        start_date, end_date = date_filter
        where_clauses.append("transaction_date BETWEEN ? AND ?")
        params.extend([start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')])
    
    base_query = """
    SELECT 
        st.transaction_date as Date,
        p.product_name as Product,
        p.category as Category,
        r.region_name as Region,
        st.sales_rep as Sales_Rep,
        st.quantity as Quantity,
        st.unit_price as Unit_Price,
        st.total_sales as Total_Sales,
        st.profit as Profit,
        st.margin_percent as Margin_Percent,
        st.customer_id as Customer_ID,
        st.order_id as Order_ID,
        st.day_of_week as Day_Of_Week,
        st.month as Month,
        st.quarter as Quarter,
        st.is_weekend as Is_Weekend,
        c.customer_segment as Customer_Segment
    FROM sales_transactions st
    JOIN products p ON st.product_id = p.product_id
    JOIN regions r ON st.region_id = r.region_id
    JOIN customers c ON st.customer_id = c.customer_id
    """
    
    if where_clauses:
        base_query += " WHERE " + " AND ".join(where_clauses)
    
    base_query += " ORDER BY st.transaction_date DESC"
    
    result = db.run_custom_query(base_query, params)
    
    if result["success"] and result["data"]:
        df = pd.DataFrame(result["data"])
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    else:
        st.error(f"Failed to load data: {result.get('error', 'Unknown error')}")
        return pd.DataFrame()

# ==================== SIDEBAR FILTERS ====================
st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Dashboard Filters")

# Date Range
st.sidebar.subheader("📅 Date Range")
min_date = datetime(2024, 1, 1).date()
max_date = datetime(2024, 6, 30).date()
selected_dates = st.sidebar.slider(
    "Select Date Range:",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date),
    format="YYYY-MM-DD"
)

# Product Filter
st.sidebar.subheader("📦 Product Filter")
product_query = "SELECT DISTINCT product_name FROM products ORDER BY product_name"
products_result = db.run_custom_query(product_query)
product_options = [row['product_name'] for row in products_result['data']] if products_result['success'] else []
selected_products = st.sidebar.multiselect(
    "Select Products:",
    options=product_options,
    default=product_options[:3] if product_options else []
)

# Region Filter
st.sidebar.subheader("🌍 Region Filter")
region_query = "SELECT region_name FROM regions ORDER BY region_name"
regions_result = db.run_custom_query(region_query)
region_options = [row['region_name'] for row in regions_result['data']] if regions_result['success'] else []
selected_regions = st.sidebar.multiselect(
    "Select Regions:",
    options=region_options,
    default=region_options
)

# Category Filter
st.sidebar.subheader("🗂️ Category Filter")
category_query = "SELECT DISTINCT category FROM products ORDER BY category"
categories_result = db.run_custom_query(category_query)
category_options = [row['category'] for row in categories_result['data']] if categories_result['success'] else []
selected_categories = st.sidebar.multiselect(
    "Select Categories:",
    options=category_options,
    default=category_options
)

# ==================== MAIN DASHBOARD ====================
st.markdown('<h1 style="color: #1E3A8A;">📊 SQL Sales Analytics Dashboard</h1>', unsafe_allow_html=True)

# Database Badge
st.markdown("""
<div style="background: #f8f9fa; padding: 1rem; border-radius: 10px; margin: 1rem 0;">
    <span class='sql-badge'>SQLite Database</span>
    <span class='sql-badge'>15+ Tables/Views</span>
    <span class='sql-badge'>Parameterized Queries</span>
    <span class='sql-badge'>Database Views</span>
    <span class='sql-badge'>Foreign Keys</span>
</div>
""", unsafe_allow_html=True)

st.markdown("""
**Portfolio Project** | *Demonstrating SQL Database Integration + Full-Stack Development*  
This dashboard connects to a **relational SQLite database** with 15+ tables, views, and complex queries.
""")

# ==================== LOAD FILTERED DATA ====================
with st.spinner("🔄 Executing SQL queries with your filters..."):
    # Apply filters
    date_filter = (selected_dates[0], selected_dates[1]) if selected_dates else None
    
    # Load main data
    df = load_sales_data(date_filter=date_filter)
    
    # Apply additional filters in Python (could be done in SQL too)
    if not df.empty:
        if selected_products:
            df = df[df['Product'].isin(selected_products)]
        if selected_regions:
            df = df[df['Region'].isin(selected_regions)]
        if selected_categories:
            df = df[df['Category'].isin(selected_categories)]

# ==================== SQL METRICS ====================
st.markdown("### 📈 SQL-Powered Metrics")

if not df.empty:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_sales = df['Total_Sales'].sum()
        st.metric(
            label="Total Sales",
            value=f"${total_sales:,.0f}",
            help="SUM(total_sales) FROM sales_transactions"
        )
    
    with col2:
        avg_order = df['Total_Sales'].mean()
        st.metric(
            label="Avg Order Value",
            value=f"${avg_order:,.2f}",
            help="AVG(total_sales) FROM sales_transactions"
        )
    
    with col3:
        total_profit = df['Profit'].sum()
        st.metric(
            label="Total Profit",
            value=f"${total_profit:,.0f}",
            help="SUM(profit) FROM sales_transactions"
        )
    
    with col4:
        unique_customers = df['Customer_ID'].nunique()
        st.metric(
            label="Unique Customers",
            value=f"{unique_customers:,}",
            help="COUNT(DISTINCT customer_id) FROM sales_transactions"
        )
else:
    st.warning("No data found with current filters. Try adjusting your selections.")

# ==================== SQL QUERY SHOWCASE ====================
st.markdown("### 🔍 Live SQL Query Showcase")

tab1, tab2, tab3 = st.tabs(["📊 Visualization", "🗃️ Database Schema", "📝 Query Examples"])

with tab1:
    if not df.empty:
        # Chart 1: Sales Trend
        st.subheader("Sales Trend (SQL GROUP BY + DATE functions)")
        daily_sales = df.groupby('Date')['Total_Sales'].sum().reset_index()
        
        fig1 = px.line(
            daily_sales,
            x='Date',
            y='Total_Sales',
            title='Daily Sales Trend',
            markers=True
        )
        st.plotly_chart(fig1, use_container_width=True)
        
        # Chart 2: Product Performance
        st.subheader("Product Performance (SQL JOIN + GROUP BY)")
        product_perf = df.groupby(['Product', 'Category']).agg({
            'Total_Sales': 'sum',
            'Profit': 'sum'
        }).reset_index()
        
        fig2 = px.bar(
            product_perf.nlargest(10, 'Total_Sales'),
            x='Product',
            y='Total_Sales',
            color='Category',
            title='Top 10 Products by Sales'
        )
        st.plotly_chart(fig2, use_container_width=True)
        
        # Chart 3: Regional Analysis
        st.subheader("Regional Analysis (SQL Aggregation)")
        regional_sales = df.groupby('Region').agg({
            'Total_Sales': 'sum',
            'Profit': 'sum',
            'Order_ID': 'count'
        }).reset_index()
        
        fig3 = px.scatter(
            regional_sales,
            x='Total_Sales',
            y='Profit',
            size='Order_ID',
            color='Region',
            hover_name='Region',
            title='Regional Performance: Sales vs Profit'
        )
        st.plotly_chart(fig3, use_container_width=True)

with tab2:
    st.subheader("📐 Database Schema Design")
    
    schema_col1, schema_col2 = st.columns(2)
    
    with schema_col1:
        st.markdown("""
        **Main Tables:**
        
        **`sales_transactions`** (Core table)
        ```sql
        CREATE TABLE sales_transactions (
            transaction_id INTEGER PRIMARY KEY,
            order_id TEXT UNIQUE,
            customer_id TEXT,
            product_id INTEGER,
            region_id INTEGER,
            transaction_date DATE,
            quantity INTEGER,
            unit_price REAL,
            total_sales REAL,
            profit REAL,
            margin_percent REAL,
            -- 15+ more columns...
            FOREIGN KEY (customer_id) REFERENCES customers,
            FOREIGN KEY (product_id) REFERENCES products,
            FOREIGN KEY (region_id) REFERENCES regions
        )
        ```
        
        **`products`** (Product catalog)
        ```sql
        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY,
            product_name TEXT,
            category TEXT,
            base_price REAL,
            cost_price REAL,
            supplier TEXT
        )
        ```
        """)
    
    with schema_col2:
        st.markdown("""
        **Supporting Tables:**
        
        **`customers`** (Customer data)
        ```sql
        CREATE TABLE customers (
            customer_id TEXT PRIMARY KEY,
            customer_name TEXT,
            email TEXT,
            region_id INTEGER,
            customer_segment TEXT,
            total_purchases REAL
        )
        ```
        
        **`regions`** (Regional data)
        ```sql
        CREATE TABLE regions (
            region_id INTEGER PRIMARY KEY,
            region_name TEXT UNIQUE,
            manager TEXT,
            target_sales REAL
        )
        ```
        
        **Database Views:**
        - `daily_sales_summary`
        - `top_products_view`
        - `customer_lifetime_value`
        """)
    
    st.info("💡 This normalized schema demonstrates proper database design with foreign keys, indexes, and views.")

with tab3:
    st.subheader("📝 Example SQL Queries")
    
    query_examples = {
        "Complex JOIN with Aggregation": """
            -- Sales by product category and region
            SELECT 
                p.category,
                r.region_name,
                COUNT(*) as transaction_count,
                SUM(st.total_sales) as total_sales,
                AVG(st.margin_percent) as avg_margin
            FROM sales_transactions st
            JOIN products p ON st.product_id = p.product_id
            JOIN regions r ON st.region_id = r.region_id
            WHERE st.transaction_date >= '2024-01-01'
            GROUP BY p.category, r.region_name
            HAVING total_sales > 10000
            ORDER BY total_sales DESC
        """,
        
        "Customer Analysis": """
            -- Customer lifetime value analysis
            SELECT 
                c.customer_segment,
                COUNT(DISTINCT c.customer_id) as customer_count,
                SUM(st.total_sales) as total_revenue,
                AVG(st.total_sales) as avg_customer_value,
                MIN(st.transaction_date) as first_purchase,
                MAX(st.transaction_date) as last_purchase
            FROM customers c
            JOIN sales_transactions st ON c.customer_id = st.customer_id
            GROUP BY c.customer_segment
            ORDER BY total_revenue DESC
        """,
        
        "Time Series Analysis": """
            -- Monthly sales trend with growth
            WITH monthly_sales AS (
                SELECT 
                    strftime('%Y-%m', transaction_date) as month,
                    SUM(total_sales) as monthly_sales
                FROM sales_transactions
                GROUP BY strftime('%Y-%m', transaction_date)
            )
            SELECT 
                month,
                monthly_sales,
                LAG(monthly_sales) OVER (ORDER BY month) as prev_month_sales,
                ROUND(
                    (monthly_sales - LAG(monthly_sales) OVER (ORDER BY month)) / 
                    LAG(monthly_sales) OVER (ORDER BY month) * 100, 2
                ) as growth_percent
            FROM monthly_sales
            ORDER BY month
        """
    }
    
    selected_example = st.selectbox("Choose a query example:", list(query_examples.keys()))
    
    st.code(query_examples[selected_example], language="sql")
    
    if st.button("Run This Example"):
        with st.spinner("Executing complex SQL query..."):
            result = db.run_custom_query(query_examples[selected_example])
            if result["success"]:
                st.success(f"✅ Query returned {result['row_count']} rows")
                if result["data"]:
                    df_result = pd.DataFrame(result["data"])
                    st.dataframe(df_result, use_container_width=True)

# ==================== DATA EXPLORATION ====================
st.markdown("### 🔎 Interactive Data Exploration")

if not df.empty:
    explore_col1, explore_col2 = st.columns([2, 1])
    
    with explore_col1:
        st.subheader("Filtered Transaction Data")
        st.dataframe(
            df.head(100),
            use_container_width=True,
            column_config={
                "Date": st.column_config.DatetimeColumn(format="YYYY-MM-DD"),
                "Unit_Price": st.column_config.NumberColumn(format="$%.2f"),
                "Total_Sales": st.column_config.NumberColumn(format="$%.2f"),
                "Profit": st.column_config.NumberColumn(format="$%.2f"),
                "Margin_Percent": st.column_config.NumberColumn(format="%.1f%%")
            }
        )
        st.caption(f"Showing 100 of {len(df):,} filtered records")
    
    with explore_col2:
        st.subheader("Data Statistics")
        
        # Basic stats
        stats_df = df[['Total_Sales', 'Profit', 'Margin_Percent', 'Quantity']].describe()
        st.dataframe(stats_df.round(2), use_container_width=True)
        
        # Unique counts
        st.metric("Unique Products", df['Product'].nunique())
        st.metric("Unique Regions", df['Region'].nunique())
        
        # Export options
        st.subheader("Export Data")
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"sales_data_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

# ==================== TECHNICAL SKILLS DEMONSTRATION ====================
st.markdown("---")
st.markdown("### 🛠️ Technical Skills Demonstrated")

tech_col1, tech_col2, tech_col3 = st.columns(3)

with tech_col1:
    st.markdown("""
    **💻 SQL Database Skills:**
    - Database Design & Normalization
    - Complex SQL Queries (JOINs, GROUP BY, Window Functions)
    - Parameterized Queries (SQL Injection Prevention)
    - Database Indexing & Performance
    - Views & Stored Query Logic
    - Foreign Key Relationships
    """)

with tech_col2:
    st.markdown("""
    **📊 Data Science Skills:**
    - Data Processing with Pandas
    - Interactive Visualization (Plotly)
    - Statistical Analysis
    - Time Series Analysis
    - Business Intelligence Metrics
    - Data Cleaning & Transformation
    """)

with tech_col3:
    st.markdown("""
    **🌐 Software Engineering:**
    - Full-Stack Web Development (Streamlit)
    - Database Integration
    - Application Architecture
    - Caching & Performance Optimization
    - Error Handling & Validation
    - Professional Documentation
    """)

# ==================== DATABASE ADMIN SECTION ====================
with st.expander("⚙️ Database Administration", expanded=False):
    admin_tab1, admin_tab2 = st.tabs(["Database Operations", "Query Any Table"])
    
    with admin_tab1:
        col_admin1, col_admin2 = st.columns(2)
        
        with col_admi
