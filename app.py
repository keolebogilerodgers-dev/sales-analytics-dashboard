"""
Sales Analytics Dashboard
Built by: Keolebogile Leatile Rodgers
A Streamlit web application demonstrating data processing and visualization skills.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# ==================== PAGE CONFIGURATION ====================
st.set_page_config(
    page_title="Sales Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CUSTOM CSS FOR PROFESSIONAL LOOK ====================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        margin-bottom: 1rem;
    }
    .kpi-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .section-header {
        font-size: 1.5rem;
        color: #374151;
        border-left: 5px solid #3B82F6;
        padding-left: 15px;
        margin: 2rem 0 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ==================== DATA GENERATION & LOADING ====================
@st.cache_data
def generate_sales_data():
    """Generate a realistic sales dataset for demonstration."""
    np.random.seed(42)
    
    # Generate 6 months of daily data
    dates = pd.date_range(start='2024-01-01', end='2024-06-30', freq='D')
    
    products = ['Laptop', 'Smartphone', 'Tablet', 'Monitor', 'Headphones', 'Keyboard']
    regions = ['North America', 'Europe', 'Asia Pacific', 'Latin America']
    categories = ['Electronics', 'Computers', 'Accessories']
    
    data = []
    for date in dates:
        for _ in range(np.random.randint(20, 40)):  # Daily transactions
            product = np.random.choice(products)
            region = np.random.choice(regions)
            
            # Base pricing
            price_map = {
                'Laptop': 899.99, 'Smartphone': 699.99, 'Tablet': 399.99,
                'Monitor': 249.99, 'Headphones': 149.99, 'Keyboard': 79.99
            }
            
            base_price = price_map[product]
            quantity = np.random.randint(1, 4)
            
            # Add some seasonality and trends
            day_of_week = date.dayofweek
            weekend_multiplier = 1.3 if day_of_week >= 5 else 1.0
            price_variation = np.random.uniform(0.9, 1.1)
            
            sales_amount = base_price * quantity * weekend_multiplier * price_variation
            
            data.append({
                'Date': date,
                'Product': product,
                'Region': region,
                'Category': 'Electronics' if product in ['Laptop', 'Smartphone', 'Tablet'] 
                          else 'Computers' if product == 'Monitor' 
                          else 'Accessories',
                'Quantity': quantity,
                'Unit_Price': base_price * price_variation,
                'Sales': sales_amount,
                'Customer_ID': f"CUST{np.random.randint(1000, 9999)}",
                'Day_Of_Week': date.strftime('%A'),
                'Month': date.strftime('%B'),
                'Week_Number': date.isocalendar().week
            })
    
    df = pd.DataFrame(data)
    
    # Add some missing values for realistic data cleaning demonstration
    if len(df) > 100:
        idx_to_null = np.random.choice(df.index, size=10, replace=False)
        df.loc[idx_to_null, 'Region'] = None
    
    return df

# Load the data
df = generate_sales_data()

# ==================== SIDEBAR FILTERS ====================
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2103/2103655.png", width=80)
st.sidebar.title("🔍 Dashboard Controls")

# Date range filter
st.sidebar.subheader("Date Range")
min_date, max_date = st.sidebar.slider(
    "Select Date Range:",
    min_value=df['Date'].min().date(),
    max_value=df['Date'].max().date(),
    value=(df['Date'].min().date(), df['Date'].max().date()),
    format="YYYY-MM-DD"
)

# Product multi-select
st.sidebar.subheader("Product Selection")
selected_products = st.sidebar.multiselect(
    "Choose Products:",
    options=sorted(df['Product'].unique()),
    default=sorted(df['Product'].unique())[:3]
)

# Region selector
st.sidebar.subheader("Region Filter")
selected_regions = st.sidebar.multiselect(
    "Choose Regions:",
    options=sorted([r for r in df['Region'].unique() if pd.notna(r)]),
    default=sorted([r for r in df['Region'].unique() if pd.notna(r)])
)

# ==================== APPLY FILTERS ====================
filtered_df = df[
    (df['Date'].dt.date >= min_date) &
    (df['Date'].dt.date <= max_date)
]

if selected_products:
    filtered_df = filtered_df[filtered_df['Product'].isin(selected_products)]
if selected_regions:
    filtered_df = filtered_df[filtered_df['Region'].isin(selected_regions)]

# ==================== MAIN DASHBOARD LAYOUT ====================
st.markdown('<h1 class="main-header">📊 Sales Analytics Dashboard</h1>', unsafe_allow_html=True)
st.markdown("""
*Interactive dashboard for exploring sales performance, trends, and customer insights.*  
**Skills Demonstrated:** Data Processing, Visualization, Web Application Development, Business Intelligence
""")

# ==================== KPI METRICS ROW ====================
st.markdown('<h2 class="section-header">📈 Key Performance Indicators</h2>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_sales = filtered_df['Sales'].sum()
    st.metric(
        label="Total Sales",
        value=f"${total_sales:,.0f}",
        delta=f"${total_sales - df['Sales'].sum()/2:,.0f}"
    )

with col2:
    avg_order = filtered_df['Sales'].mean()
    st.metric(
        label="Average Order Value",
        value=f"${avg_order:,.2f}",
        delta=f"${avg_order - df['Sales'].mean()/1.5:,.2f}"
    )

with col3:
    total_transactions = len(filtered_df)
    st.metric(
        label="Total Transactions",
        value=f"{total_transactions:,}",
        delta=f"{total_transactions - len(df)/2:,.0f}"
    )

with col4:
    top_product = filtered_df.groupby('Product')['Sales'].sum().idxmax()
    st.metric(
        label="Top Product",
        value=top_product,
        delta=None
    )

# ==================== VISUALIZATION SECTION ====================
st.markdown('<h2 class="section-header">📊 Data Visualizations</h2>', unsafe_allow_html=True)

# First row of charts
col1, col2 = st.columns(2)

with col1:
    st.subheader("Sales Trend Over Time")
    daily_sales = filtered_df.groupby('Date')['Sales'].sum().reset_index()
    fig1 = px.line(
        daily_sales, 
        x='Date', 
        y='Sales',
        markers=True,
        template='plotly_white'
    )
    fig1.update_layout(
        xaxis_title="Date",
        yaxis_title="Sales ($)",
        hovermode='x unified'
    )
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("Sales by Product Category")
    category_sales = filtered_df.groupby('Category')['Sales'].sum().reset_index()
    fig2 = px.pie(
        category_sales,
        values='Sales',
        names='Category',
        hole=0.4,
        color_discrete_sequence=px.colors.sequential.RdBu
    )
    fig2.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig2, use_container_width=True)

# Second row of charts
col3, col4 = st.columns(2)

with col3:
    st.subheader("Regional Performance")
    region_sales = filtered_df.groupby('Region')['Sales'].sum().reset_index()
    fig3 = px.bar(
        region_sales.sort_values('Sales', ascending=True),
        y='Region',
        x='Sales',
        orientation='h',
        color='Sales',
        color_continuous_scale='Viridis'
    )
    fig3.update_layout(
        yaxis_title="",
        xaxis_title="Sales ($)"
    )
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.subheader("Product Performance Heatmap")
    pivot_data = filtered_df.pivot_table(
        values='Sales',
        index='Product',
        columns='Month',
        aggfunc='sum',
        fill_value=0
    )
    fig4 = px.imshow(
        pivot_data,
        labels=dict(x="Month", y="Product", color="Sales"),
        color_continuous_scale='RdBu_r',
        aspect='auto'
    )
    st.plotly_chart(fig4, use_container_width=True)

# ==================== DATA EXPLORATION SECTION ====================
st.markdown('<h2 class="section-header">🔍 Data Exploration</h2>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📋 Sample Data", "📈 Statistical Summary", "📥 Export Options"])

with tab1:
    st.subheader("Filtered Data Preview")
    st.dataframe(
        filtered_df.sort_values('Date', ascending=False).head(20),
        use_container_width=True,
        column_config={
            "Date": st.column_config.DatetimeColumn(format="YYYY-MM-DD"),
            "Sales": st.column_config.NumberColumn(format="$%.2f"),
            "Unit_Price": st.column_config.NumberColumn(format="$%.2f")
        }
    )

with tab2:
    st.subheader("Statistical Summary")
    if not filtered_df.empty:
        st.write("**Numerical Columns:**")
        st.dataframe(filtered_df[['Sales', 'Quantity', 'Unit_Price']].describe())
        
        st.write("**Missing Values Check:**")
        missing_data = filtered_df.isnull().sum()
        st.dataframe(missing_data[missing_data > 0].reset_index().rename(
            columns={'index': 'Column', 0: 'Missing Values'}
        ))

with tab3:
    st.subheader("Export Your Analysis")
    
    # Convert DataFrame to different formats
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    json_str = filtered_df.to_json(orient='records', date_format='iso')
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"sales_data_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    with col2:
        st.download_button(
            label="📥 Download as JSON",
            data=json_str,
            file_name=f"sales_data_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )
    
    st.info("💡 *This demonstrates data export functionality, a key feature in enterprise applications.*")

# ==================== FOOTER & TECHNICAL NOTES ====================
st.markdown("---")
st.markdown("""
### 🛠️ Technical Implementation Notes
**Built with:** Streamlit, Pandas, Plotly, NumPy  
**Skills Demonstrated:** 
- **Data Processing:** Generated and cleaned realistic sales data
- **Web Development:** Created interactive dashboard with filters and controls
- **Data Visualization:** Implemented multiple chart types (line, bar, pie, heatmap)
- **Software Engineering:** Structured code with functions, caching, and error handling
- **Business Intelligence:** Designed KPIs and metrics for decision-making

**For Recruiters:** This project bridges my Business Intelligence background with software engineering skills, demonstrating ability to build data-driven web applications.
""")

# Add a refresh button
if st.button("🔄 Refresh Data & Visualizations"):
    st.cache_data.clear()
    st.rerun()
