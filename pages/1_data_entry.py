import streamlit as st
from datetime import datetime
import sys
from pathlib import Path
import pandas as pd
import io

# Add the root directory to Python path
root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

from database.db_manager import (
    save_transaction,
    save_fixed_transaction,
    get_transactions,
    check_category_threshold,
    get_all_categories
)
from utils.helpers import format_amount, format_currency

st.set_page_config(
    page_title="Data Entry - Money Manager",
    page_icon="📝",
    layout="wide"
)

st.title("Enter New Transaction 📝")

# Get all categories (including custom ones)
CATEGORIES = get_all_categories()

# Create tabs for different entry methods
tab1, tab2, tab3 = st.tabs(["Regular Transaction", "Fixed Monthly Transaction", "Bulk Import"])

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

# Bulk Import Tab
with tab3:
    st.subheader("Import Transactions from CSV")
    
    # Add instructions
    st.markdown("""
    ### CSV File Requirements:
    - The CSV file should have the following columns:
        - date (YYYY-MM-DD format)
        - type (Income/Expense)
        - category
        - amount (positive number)
        - comment (optional)
    - The first row should be the header row
    """)
    
    # File uploader
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    if uploaded_file is not None:
        try:
            # Read CSV file
            df = pd.read_csv(uploaded_file)
            
            # Display preview of the data
            st.subheader("Preview of uploaded data")
            st.dataframe(df.head(), use_container_width=True)
            
            # Validate columns
            required_columns = ['date', 'type', 'category', 'amount', 'comment']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.error(f"Missing required columns: {', '.join(missing_columns)}")
            else:
                # Validate data types and format
                validation_errors = []
                
                # Check date format
                try:
                    pd.to_datetime(df['date'])
                except:
                    validation_errors.append("Date column should be in YYYY-MM-DD format")
                
                # Check transaction types
                invalid_types = df[~df['type'].isin(['Income', 'Expense'])]['type'].unique()
                if len(invalid_types) > 0:
                    validation_errors.append(f"Invalid transaction types found: {', '.join(invalid_types)}")
                
                # Check categories
                valid_categories = get_all_categories()
                invalid_categories = df[~df['category'].isin(valid_categories)]['category'].unique()
                if len(invalid_categories) > 0:
                    validation_errors.append(f"Invalid categories found: {', '.join(invalid_categories)}")
                
                # Check amounts
                if not pd.to_numeric(df['amount'], errors='coerce').notnull().all():
                    validation_errors.append("All amounts must be valid numbers")
                
                if validation_errors:
                    st.error("Validation errors found:")
                    for error in validation_errors:
                        st.write(f"- {error}")
                else:
                    # Add import button
                    if st.button("Import Transactions", type="primary"):
                        success_count = 0
                        error_count = 0
                        
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        for index, row in df.iterrows():
                            try:
                                # Format amount based on transaction type
                                amount = abs(float(row['amount']))
                                formatted_amount = format_amount(amount, row['type'])
                                
                                # Save transaction
                                if save_transaction(
                                    row['date'],
                                    row['type'],
                                    row['category'],
                                    formatted_amount,
                                    str(row['comment']) if pd.notna(row['comment']) else "-"
                                ):
                                    success_count += 1
                                else:
                                    error_count += 1
                                
                                # Update progress
                                progress = (index + 1) / len(df)
                                progress_bar.progress(progress)
                                status_text.text(f"Processing transactions... {index + 1}/{len(df)}")
                                
                            except Exception as e:
                                error_count += 1
                                st.error(f"Error processing row {index + 1}: {str(e)}")
                        
                        # Show final results
                        if success_count > 0:
                            st.success(f"""
                            Import completed!
                            - Successfully imported: {success_count} transactions
                            - Failed to import: {error_count} transactions
                            """)
                            if success_count == len(df):
                                st.balloons()
                        else:
                            st.error("Failed to import any transactions. Please check the data and try again.")
                        
        except Exception as e:
            st.error(f"Error reading CSV file: {str(e)}")
            st.info("Please make sure your CSV file is properly formatted and try again.")