import streamlit as st
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path
import calendar

# Add the root directory to Python path
root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

from database.db_manager import (
    get_transactions,
    get_category_thresholds,
    update_category_threshold,
)
from utils.helpers import format_currency

st.set_page_config(
    page_title="Budget Planning - Money Manager",
    page_icon="📊",
    layout="wide"
)

st.title("Budget Planning 📊")

# Create tabs for different budget features
tab1, tab2 = st.tabs(["Budget Planning", "Budget Tracking"])

with tab1:
    st.subheader("Set Monthly Budget")
    
    # Get current budget/thresholds
    current_thresholds = get_category_thresholds()
    
    # Create columns for better layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Budget setting form
        with st.form("budget_form"):
            CATEGORIES = [
                "Housing", "Transportation", "Groceries", "Food & Dining",
                "Shopping", "Entertainment", "Healthcare", "Education",
                "Utilities", "Insurance", "Savings", "Investments", "Other"
            ]
            
            st.write("Set monthly budget limits for each category:")
            
            # Create three columns for category inputs
            budget_cols = st.columns(3)
            budgets = {}
            
            for i, category in enumerate(CATEGORIES):
                col_idx = i % 3
                with budget_cols[col_idx]:
                    # Get current value safely
                    current_value = current_thresholds[
                        current_thresholds['category'] == category
                    ]['monthly_limit'].iloc[0] if len(current_thresholds[
                        current_thresholds['category'] == category
                    ]) > 0 else 0.0
                    
                    budgets[category] = st.number_input(
                        f"{category}",
                        min_value=0.0,
                        value=float(current_value),
                        step=50.0,
                        key=f"budget_{category}",
                        help=f"Set monthly budget limit for {category}"
                    )
            
            submitted = st.form_submit_button(
                "Save Budget",
                use_container_width=True,
                type="primary"
            )
            
            if submitted:
                success = True
                for category, amount in budgets.items():
                    if not update_category_threshold(category, amount):
                        success = False
                        break
                
                if success:
                    st.success("Budget updated successfully! 🎯")
                    st.balloons()
                else:
                    st.error("Error updating budget. Please try again.")
    
    with col2:
        st.write("Budget Tips")
        st.info("""
        💡 Common budget allocations:
        - Housing: 25-35%
        - Transportation: 10-15%
        - Food: 10-15%
        - Utilities: 5-10%
        - Insurance: 10-15%
        - Savings: 10-15%
        - Other: 10-20%
        """)
        
        # Add a note about budget tracking
        st.write("About Budget Tracking")
        st.markdown("""
        - Set budget limits for categories you want to monitor
        - Leave a budget at 0 to disable tracking for that category
        - You'll receive notifications when approaching limits
        - Track your progress in the Budget Tracking tab
        """)

with tab2:
    st.subheader("Budget Tracking")
    
    # Get transactions
    df = get_transactions()
    
    if not df.empty:
        # Convert date to datetime
        df['date'] = pd.to_datetime(df['date'])
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # Allow user to select month and year
        col1, col2 = st.columns(2)
        with col1:
            selected_year = st.selectbox(
                "Select Year",
                options=sorted(df['date'].dt.year.unique(), reverse=True),
                index=0
            )
        with col2:
            selected_month = st.selectbox(
                "Select Month",
                options=range(1, 13),
                format_func=lambda x: calendar.month_name[x],
                index=current_month - 1 if selected_year == current_year else 0
            )
        
        # Filter for selected month
        mask = (df['date'].dt.month == selected_month) & \
               (df['date'].dt.year == selected_year)
        current_data = df[mask]
        
        # Calculate spending by category
        category_spending = current_data[
            current_data['type'] == 'Expense'
        ].groupby('category')['amount'].sum().abs()
        
        # Get budget limits
        budget_df = get_category_thresholds()
        
        # Create progress bars for each category
        st.write(f"Budget Progress - {calendar.month_name[selected_month]} {selected_year}")
        
        if not category_spending.empty:
            total_budget = 0
            total_spent = 0
            
            for category in CATEGORIES:
                budget_limit = budget_df[
                    budget_df['category'] == category
                ]['monthly_limit'].iloc[0] if len(budget_df[
                    budget_df['category'] == category
                ]) > 0 else 0.0
                
                current_spent = category_spending.get(category, 0)
                
                if budget_limit > 0:  # Only show categories with budget set
                    total_budget += budget_limit
                    total_spent += current_spent
                    
                    progress = min(current_spent / budget_limit * 100, 100)
                    
                    # Determine color based on progress
                    color = (
                        "normal" if progress <= 75 
                        else "warning" if progress <= 90 
                        else "error"
                    )
                    
                    st.write(f"**{category}**")
                    
                    # Create progress bar
                    progress_container = st.container()
                    progress_container.progress(
                        progress / 100,
                        text=f"{progress:.1f}%"
                    )
                    
                    # Display metrics
                    col1, col2, col3 = st.columns(3)
                    col1.metric(
                        "Spent",
                        format_currency(current_spent)
                    )
                    col2.metric(
                        "Budget",
                        format_currency(budget_limit)
                    )
                    col3.metric(
                        "Remaining",
                        format_currency(max(budget_limit - current_spent, 0))
                    )
                    
                    # Add warning if over budget
                    if progress > 90:
                        st.warning(
                            f"⚠️ {category} spending is at {progress:.1f}% of budget!"
                        )
                    
                    st.divider()
            
            # Display total budget summary
            st.subheader("Total Budget Summary")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Total Budget",
                    format_currency(total_budget)
                )
            
            with col2:
                st.metric(
                    "Total Spent",
                    format_currency(total_spent)
                )
            
            with col3:
                progress = (total_spent / total_budget * 100) if total_budget > 0 else 0
                st.metric(
                    "Overall Progress",
                    f"{progress:.1f}%",
                    format_currency(total_budget - total_spent)
                )
            
            # Add overall warning if needed
            if progress > 90:
                st.error(
                    "⚠️ Warning: Overall spending is over 90% of total budget!"
                )
            elif progress > 75:
                st.warning(
                    "⚠️ Note: Overall spending is over 75% of total budget."
                )
        else:
            st.info(
                f"No expenses found for {calendar.month_name[selected_month]} {selected_year}"
            )
    else:
        st.info(
            """No transactions found. Add some transactions and set budgets to start tracking!
            
            1. Use the Budget Planning tab to set category budgets
            2. Add transactions in the Data Entry page
            3. Come back here to track your progress
            """
        )