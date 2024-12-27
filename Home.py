import streamlit as st
from datetime import datetime
import calendar
import sys
from pathlib import Path
import pandas as pd
# Add the root directory to Python path
root_path = Path(__file__).parent
sys.path.append(str(root_path))

from database.db_manager import (
    init_db,
    init_settings_tables,
    get_transactions,
    get_category_thresholds
)
from utils.helpers import format_currency

# Configure the page
st.set_page_config(
    page_title="Money Manager",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database and settings
init_db()
init_settings_tables()

# Main title
st.title("Welcome to Money Manager 💰")

# Quick Stats Section
def display_quick_stats():
    df = get_transactions()
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # Filter for current month
        current_month_mask = (df['date'].dt.month == current_month) & \
                           (df['date'].dt.year == current_year)
        current_month_data = df[current_month_mask]
        
        # Calculate metrics
        current_month_income = current_month_data[
            current_month_data['type'] == 'Income'
        ]['amount'].sum()
        current_month_expenses = abs(current_month_data[
            current_month_data['type'] == 'Expense'
        ]['amount'].sum())
        current_month_balance = current_month_income - current_month_expenses
        
        # Display metrics
        st.subheader(f"Quick Stats - {calendar.month_name[current_month]} {current_year}")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Monthly Income",
                format_currency(current_month_income),
                help="Total income for the current month"
            )
        
        with col2:
            st.metric(
                "Monthly Expenses",
                format_currency(current_month_expenses),
                help="Total expenses for the current month"
            )
        
        with col3:
            st.metric(
                "Monthly Balance",
                format_currency(current_month_balance),
                delta=format_currency(current_month_balance),
                delta_color="normal" if current_month_balance >= 0 else "inverse",
                help="Net balance for the current month"
            )
        
        with col4:
            st.metric(
                "Transactions",
                len(current_month_data),
                help="Number of transactions this month"
            )
        
        # Check budget alerts
        budget_df = get_category_thresholds()
        if not budget_df.empty:
            expenses_by_category = current_month_data[
                current_month_data['type'] == 'Expense'
            ].groupby('category')['amount'].sum().abs()
            
            alerts = []
            for category in expenses_by_category.index:
                budget_limit = budget_df[
                    budget_df['category'] == category
                ]['monthly_limit'].iloc[0] if len(budget_df[
                    budget_df['category'] == category
                ]) > 0 else 0.0
                
                if budget_limit > 0:
                    spent = expenses_by_category[category]
                    percentage = (spent / budget_limit) * 100
                    
                    if percentage >= 90:
                        alerts.append({
                            'category': category,
                            'spent': spent,
                            'budget': budget_limit,
                            'percentage': percentage
                        })
            
            if alerts:
                st.warning("⚠️ Budget Alerts")
                for alert in alerts:
                    st.markdown(f"""
                    - **{alert['category']}**: Spent {format_currency(alert['spent'])} 
                    of {format_currency(alert['budget'])} 
                    ({alert['percentage']:.1f}% of budget)
                    """)

# Main content sections
tab1, tab2 = st.tabs(["Getting Started", "Quick Stats"])

with tab1:
    st.markdown("""
    ### Welcome to your personal Money Manager! 🌟
    
    This application helps you:
    - 📝 Track your daily expenses and income
    - 📊 View detailed transaction history
    - 📈 Analyze spending patterns
    - 💰 Set and monitor budgets
    - 📑 Generate financial reports
    
    #### Features Available
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Data Management**
        - Add regular and recurring transactions
        - Categorize income and expenses
        - Search and filter transactions
        - Export data to CSV or Excel
        
        **Analysis Tools**
        - View daily spending patterns
        - Analyze category-wise expenses
        - Track monthly trends
        - Monitor budget vs actual spending
        """)
    
    with col2:
        st.markdown("""
        **Budgeting Features**
        - Set monthly category budgets
        - Track budget utilization
        - Receive overspending alerts
        - View budget vs actual reports
        
        **Reporting Capabilities**
        - Generate monthly reports
        - Create yearly summaries
        - Export detailed reports
        - Visualize financial trends
        """)
    
    st.markdown("""
    #### Getting Started
    
    1. **Set Up Your Budgets**
       - Visit the Budget Planning page
       - Set monthly limits for each category
       - Monitor your spending against these limits
    
    2. **Record Transactions**
       - Use the Data Entry page
       - Add both regular and recurring transactions
       - Categorize your income and expenses
    
    3. **Track Your Progress**
       - Check the Transaction Management page
       - View and analyze your spending patterns
       - Generate reports for better insights
    
    4. **Review Reports**
       - Visit the Reports page
       - Analyze monthly and yearly trends
       - Export data for external use
    """)

with tab2:
    display_quick_stats()

# Add a footer with helpful links
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>Need help? Check out these resources:</p>
    <p>
        <a href="?page=data_entry">Add Transaction</a> •
        <a href="?page=view_transactions">View Transactions</a> •
        <a href="?page=budget_planning">Budget Planning</a> •
        <a href="?page=reports">Reports</a>
    </p>
</div>
""", unsafe_allow_html=True)

# Session state initialization for first-time users
if 'first_visit' not in st.session_state:
    st.session_state.first_visit = True
    st.balloons()
    st.success("""
    👋 Welcome to Money Manager! 
    
    Get started by adding your first transaction in the Data Entry page.
    
    Use the sidebar menu to navigate between different features.
    """)