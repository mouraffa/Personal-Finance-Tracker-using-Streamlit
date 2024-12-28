import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Add the root directory to Python path
root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

from database.db_manager import get_transactions, DB_PATH, get_all_categories
from utils.helpers import format_currency

st.set_page_config(
    page_title="View Transactions - Money Manager",
    page_icon="📊",
    layout="wide"
)

st.title("View Transactions 📊")

# Get transactions
df = get_transactions()

if not df.empty:
    # Check if 'category' column exists, if not, add it with default value
    if 'category' not in df.columns:
        df['category'] = 'Other'  # Add default category for old entries
    
    # Add filters in an expander
    with st.expander("Filters", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            # Date filter
            date_range = st.date_input(
                "Select Date Range",
                [pd.to_datetime(df['date']).min(), pd.to_datetime(df['date']).max()],
                key='date_range'
            )
        
        with col2:
            # Transaction type filter
            trans_type = st.multiselect(
                "Transaction Type",
                ["Income", "Expense"],
                ["Income", "Expense"]
            )

    # Get all categories (including custom ones)
    categories = sorted(get_all_categories())
    
    # Add category filter
    if len(categories) > 1:
        selected_categories = st.multiselect(
            "Categories",
            categories,
            categories
        )
        
        # Filter by category
        mask = (
            (pd.to_datetime(df['date']).dt.date >= date_range[0]) &
            (pd.to_datetime(df['date']).dt.date <= date_range[1]) &
            (df['type'].isin(trans_type)) &
            (df['category'].isin(selected_categories))
        )
    else:
        # Filter without category if we don't have meaningful categories
        mask = (
            (pd.to_datetime(df['date']).dt.date >= date_range[0]) &
            (pd.to_datetime(df['date']).dt.date <= date_range[1]) &
            (df['type'].isin(trans_type))
        )
    
    filtered_df = df.loc[mask].copy()
    
    # Sort by date
    filtered_df['date'] = pd.to_datetime(filtered_df['date'])
    filtered_df = filtered_df.sort_values('date', ascending=False)
    
    # Display summary metrics
    st.subheader("Summary")
    
    # Summary by type (Income/Expense)
    col1, col2, col3 = st.columns(3)
    
    total_income = filtered_df[filtered_df['type'] == 'Income']['amount'].sum()
    total_expense = abs(filtered_df[filtered_df['type'] == 'Expense']['amount'].sum())
    balance = total_income - total_expense
    
    col1.metric(
        "Total Income",
        format_currency(total_income),
        delta=None
    )
    
    col2.metric(
        "Total Expenses",
        format_currency(total_expense),
        delta=None
    )
    
    col3.metric(
        "Balance",
        format_currency(balance),
        delta=format_currency(balance) if balance != 0 else None,
        delta_color="normal" if balance >= 0 else "inverse"
    )
    
    # Show category breakdown only if we have meaningful categories
    if len(categories) > 1:
        # Summary by category
        st.subheader("Category Breakdown")
        
        # Create two columns for Income and Expense category breakdowns
        cat_col1, cat_col2 = st.columns(2)
        
        with cat_col1:
            st.write("Income by Category")
            income_by_cat = filtered_df[filtered_df['type'] == 'Income'].groupby('category')['amount'].sum()
            if not income_by_cat.empty:
                income_df = pd.DataFrame({
                    'Category': income_by_cat.index,
                    'Amount': income_by_cat.values
                })
                income_df['Amount'] = income_df['Amount'].apply(format_currency)
                st.dataframe(income_df, use_container_width=True, hide_index=True)
            else:
                st.info("No income transactions in selected period")
        
        with cat_col2:
            st.write("Expenses by Category")
            expense_by_cat = filtered_df[filtered_df['type'] == 'Expense'].groupby('category')['amount'].sum()
            if not expense_by_cat.empty:
                expense_df = pd.DataFrame({
                    'Category': expense_by_cat.index,
                    'Amount': [abs(val) for val in expense_by_cat.values]
                })
                expense_df['Amount'] = expense_df['Amount'].apply(format_currency)
                st.dataframe(expense_df, use_container_width=True, hide_index=True)
            else:
                st.info("No expense transactions in selected period")
    
    # Display all transactions
    st.subheader("All Transactions")
    
    # Format the dataframe for display
    display_df = filtered_df.copy()
    display_df['amount'] = display_df['amount'].apply(format_currency)
    display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
    
    # Rename columns for display
    column_rename = {
        'date': 'Date',
        'type': 'Type',
        'amount': 'Amount',
        'comment': 'Comment'
    }
    if 'category' in display_df.columns:
        column_rename['category'] = 'Category'
    
    display_df.rename(columns=column_rename, inplace=True)
    
    # Configure columns for display
    column_config = {
        "Date": st.column_config.DateColumn(
            "Date",
            help="Transaction date",
            format="YYYY-MM-DD",
        ),
        "Amount": st.column_config.TextColumn(
            "Amount",
            help="Transaction amount",
            width="medium",
        ),
        "Type": st.column_config.SelectboxColumn(
            "Type",
            help="Transaction type",
            width="small",
            options=["Income", "Expense"],
        ),
    }
    
    if 'Category' in display_df.columns:
        column_config["Category"] = st.column_config.SelectboxColumn(
            "Category",
            help="Transaction category",
            width="medium",
            options=sorted(categories),
        )
    
    # Display the dataframe with sorting enabled
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config=column_config
    )
    
else:
    st.error("""
    No transactions found. This could be due to:
    1. No transactions have been saved yet
    2. Database connection issues
    3. Database file location issues
    
    Please try adding a transaction in the Data Entry page and check if it's saved successfully.
    """)

# Add download button for the filtered data
if not df.empty:
    st.download_button(
        label="Download Data as CSV",
        data=display_df.to_csv(index=False).encode('utf-8'),
        file_name=f"transactions_{date_range[0]}_{date_range[1]}.csv",
        mime='text/csv',
    )