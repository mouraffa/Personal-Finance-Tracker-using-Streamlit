import streamlit as st
from datetime import datetime
import sys
from pathlib import Path

# Add the root directory to Python path
root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

from database.db_manager import (
    save_transaction,
    save_fixed_transaction,
    get_transactions,
    check_category_threshold
)
from utils.helpers import format_amount, format_currency

st.set_page_config(
    page_title="Data Entry - Money Manager",
    page_icon="📝",
    layout="wide"
)

st.title("Enter New Transaction 📝")

# Define categories
CATEGORIES = [
    "Housing", "Transportation", "Groceries", "Food & Dining",
    "Shopping", "Entertainment", "Healthcare", "Education",
    "Utilities", "Insurance", "Savings", "Investments",
    "Income", "Other"
]

# Create tabs for regular and fixed transactions
tab1, tab2 = st.tabs(["Regular Transaction", "Fixed Monthly Transaction"])

# Regular Transaction Tab
with tab1:
    with st.form("transaction_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            date = st.date_input(
                "Date",
                datetime.now(),
                help="Select the date of the transaction"
            )
            
            amount = st.number_input(
                "Amount",
                min_value=0.0,
                step=0.01,
                help="Enter the transaction amount"
            )
            
            category = st.selectbox(
                "Category",
                CATEGORIES,
                help="Select the transaction category"
            )
        
        with col2:
            trans_type = st.selectbox(
                "Type",
                ["Expense", "Income"],
                help="Select whether this is an income or expense"
            )
            
            comment = st.text_input(
                "Comment (optional)",
                help="Add any notes about this transaction"
            )

        # Submit button
        submitted = st.form_submit_button(
            "Save Transaction",
            use_container_width=True,
            type="primary"
        )

    if submitted:
        if amount <= 0:
            st.error("Please enter an amount greater than 0")
        else:
            # Check threshold for expenses
            threshold_warning = None
            if trans_type == "Expense":
                exceeded, threshold, current_total = check_category_threshold(
                    category, 
                    amount, 
                    date.strftime("%Y-%m-%d")
                )
                if exceeded:
                    threshold_warning = f"""
                    ⚠️ Warning: This transaction will exceed your monthly threshold for {category}!
                    - Monthly threshold: {format_currency(threshold)}
                    - Current spending: {format_currency(current_total)}
                    - This transaction: {format_currency(amount)}
                    - New total: {format_currency(current_total + amount)}
                    """
            
            # Display warning if threshold is exceeded
            if threshold_warning:
                st.warning(threshold_warning)
            
            # Save the transaction
            formatted_amount = format_amount(amount, trans_type)
            comment = comment if comment else "-"
            
            if save_transaction(
                date.strftime("%Y-%m-%d"),
                trans_type,
                category,
                formatted_amount,
                comment
            ):
                df = get_transactions()
                st.success(f"Transaction saved successfully! ✅ Total transactions: {len(df)}")
                st.balloons()

# Fixed Transaction Tab
with tab2:
    with st.form("fixed_transaction_form", clear_on_submit=True):
        st.info("Fixed transactions will be automatically added each month on the selected day.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input(
                "Start Date",
                datetime.now(),
                help="Select the start date for the recurring transaction"
            )
            
            amount = st.number_input(
                "Monthly Amount",
                min_value=0.0,
                step=0.01,
                help="Enter the monthly transaction amount"
            )
            
            category = st.selectbox(
                "Category",
                CATEGORIES,
                help="Select the transaction category",
                key="fixed_category"
            )
        
        with col2:
            trans_type = st.selectbox(
                "Type",
                ["Expense", "Income"],
                help="Select whether this is an income or expense",
                key="fixed_type"
            )
            
            comment = st.text_input(
                "Comment (optional)",
                help="Add any notes about this fixed transaction",
                key="fixed_comment"
            )

        # Submit button
        fixed_submitted = st.form_submit_button(
            "Save Fixed Transaction",
            use_container_width=True,
            type="primary"
        )

    if fixed_submitted:
        if amount <= 0:
            st.error("Please enter an amount greater than 0")
        else:
            # Check threshold for fixed expenses
            threshold_warning = None
            if trans_type == "Expense":
                exceeded, threshold, current_total = check_category_threshold(
                    category, 
                    amount, 
                    start_date.strftime("%Y-%m-%d")
                )
                if exceeded:
                    threshold_warning = f"""
                    ⚠️ Warning: This fixed transaction will exceed your monthly threshold for {category}!
                    - Monthly threshold: {format_currency(threshold)}
                    - Current spending: {format_currency(current_total)}
                    - This transaction: {format_currency(amount)}
                    - New total: {format_currency(current_total + amount)}
                    
                    Note: This warning is for the initial transaction. The same amount will be added each month.
                    """
            
            # Display warning if threshold is exceeded
            if threshold_warning:
                st.warning(threshold_warning)
            
            # Save the fixed transaction
            formatted_amount = format_amount(amount, trans_type)
            comment = comment if comment else "-"
            
            if save_fixed_transaction(
                start_date.strftime("%Y-%m-%d"),
                trans_type,
                category,
                formatted_amount,
                comment
            ):
                st.success("Fixed transaction saved successfully! ✅")
                st.info(f"This transaction will be automatically added every month on day {start_date.day}")
                st.balloons()