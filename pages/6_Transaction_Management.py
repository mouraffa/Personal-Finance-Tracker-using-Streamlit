import streamlit as st
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path
import io

# Add the root directory to Python path
root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

from database.db_manager import (
    get_transactions,
    update_transaction,
    delete_transaction,
    search_transactions,
    get_all_categories
)
from utils.helpers import format_currency

st.set_page_config(
    page_title="Transaction Management - Money Manager",
    page_icon="📝",
    layout="wide"
)

st.title("Transaction Management 📝")

# Add search functionality
st.subheader("Search Transactions")

# Create three columns for search inputs
col1, col2, col3 = st.columns(3)

with col1:
    search_term = st.text_input(
        "Search by comment or category",
        help="Enter text to search in transaction comments or categories"
    )

with col2:
    min_amount = st.number_input(
        "Minimum Amount",
        min_value=0.0,
        step=10.0,
        help="Filter transactions with amount greater than this value"
    )

with col3:
    max_amount = st.number_input(
        "Maximum Amount",
        min_value=0.0,
        step=10.0,
        help="Filter transactions with amount less than this value"
    )

# Update where we get and prepare the dataframe

# Get transactions based on search criteria
df = search_transactions(search_term, min_amount, max_amount) if any([search_term, min_amount, max_amount]) else get_transactions()

if not df.empty:
    # Make sure we only have one ID column
    if 'rowid' in df.columns and 'id' in df.columns:
        df = df.drop(columns=['rowid'])
    elif 'rowid' in df.columns:
        df = df.rename(columns={'rowid': 'id'})

    # Convert date to datetime for sorting and format display
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date', ascending=False)
    
    # Format amount for display
    display_df = df.copy()
    
    # Verify we have unique column names
    print("Column names:", display_df.columns.tolist())  # Debug print
    
    # Add formatted amount column
    display_df['formatted_amount'] = display_df['amount'].apply(format_currency)
    
    # Add delete column if not present
    if 'delete' not in display_df.columns:
        display_df['delete'] = False
        
    # Verify no duplicate column names
    assert len(display_df.columns) == len(set(display_df.columns)), "Duplicate columns found!"


# Get all categories (including custom ones)
categories = get_all_categories()

if not df.empty:
    # Convert date to datetime for sorting and format display
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date', ascending=False)
    
    # Format amount for display
    display_df = df.copy()
    display_df['formatted_amount'] = display_df['amount'].apply(format_currency)
    
    # Add delete column if not present
    if 'delete' not in display_df.columns:
        display_df['delete'] = False
    
    # Display editable dataframe
    st.subheader("Edit Transactions")
    
    # Add help text
    st.info("""
    - Edit values directly in the table
    - Check the 'Delete' box to mark transactions for deletion
    - Click 'Save Changes' when done
    - All changes will be applied at once
    """)
    
    # Create the editable dataframe
    edited_df = st.data_editor(
        display_df,
        hide_index=True,
        column_config={
            "id": st.column_config.NumberColumn(
                "ID",
                help="Transaction ID (read-only)",
                disabled=True,
                width="small"
            ),
            "date": st.column_config.DateColumn(
                "Date",
                help="Transaction date",
                min_value=datetime(2000, 1, 1),
                max_value=datetime(2100, 1, 1),
                format="YYYY-MM-DD",
                width="medium"
            ),
            "type": st.column_config.SelectboxColumn(
                "Type",
                help="Transaction type",
                options=["Income", "Expense"],
                width="small"
            ),
            "category": st.column_config.SelectboxColumn(
                "Category",
                help="Transaction category",
                options=sorted(categories),
                width="medium"
            ),
            "amount": st.column_config.NumberColumn(
                "Amount",
                help="Transaction amount",
                format="%.2f",
                width="medium"
            ),
            "formatted_amount": st.column_config.Column(
                "Formatted Amount",
                help="Formatted amount with currency symbol",
                disabled=True,
                width="medium"
            ),
            "comment": st.column_config.TextColumn(
                "Comment",
                help="Transaction comment or note",
                width="large",
                max_chars=200
            ),
            "delete": st.column_config.CheckboxColumn(
                "Delete",
                help="Select to delete this transaction",
                default=False,
                width="small"
            )
        },
        disabled=["id", "formatted_amount"],
        num_rows="dynamic"
    )
    
    # Handle save changes
    if st.button("Save Changes", type="primary"):
        try:
            changes_made = False
            success_count = 0
            error_count = 0
            
            # Handle deletions first
            rows_to_delete = edited_df[edited_df['delete'] == True]
            if not rows_to_delete.empty:
                for _, row in rows_to_delete.iterrows():
                    if delete_transaction(row['id']):
                        changes_made = True
                        success_count += 1
                    else:
                        error_count += 1
            
            # Handle updates for non-deleted rows
            rows_to_update = edited_df[edited_df['delete'] == False]
            for _, row in rows_to_update.iterrows():
                original_row = df[df['id'] == row['id']].iloc[0]
                
                # Check if any field has changed
                if any(row[field] != original_row[field] for field in ['date', 'type', 'category', 'amount', 'comment']):
                    if update_transaction(
                        row['id'],
                        row['date'].strftime('%Y-%m-%d'),
                        row['type'],
                        row['category'],
                        float(row['amount']),
                        str(row['comment'])
                    ):
                        changes_made = True
                        success_count += 1
                    else:
                        error_count += 1
            
            # Show appropriate message based on results
            if changes_made:
                if error_count == 0:
                    st.success(f"Successfully updated {success_count} transaction(s)! 🎉")
                    st.balloons()
                else:
                    st.warning(f"""
                    Partially successful update:
                    - {success_count} transaction(s) updated successfully
                    - {error_count} transaction(s) failed to update
                    """)
            else:
                if error_count > 0:
                    st.error("Failed to update any transactions. Please try again.")
                else:
                    st.info("No changes detected")
            
            # Refresh the page if changes were made
            if changes_made:
                st.rerun()
                
        except Exception as e:
            st.error(f"An error occurred while saving changes: {str(e)}")
    
    # Add export functionality
    st.subheader("Export Transactions")
    
    # Prepare export dataframe
    export_df = df.copy()
    export_df['date'] = export_df['date'].dt.strftime('%Y-%m-%d')
    export_df['amount'] = export_df['amount'].apply(format_currency)
    export_df = export_df.drop(columns=['delete']) if 'delete' in export_df.columns else export_df
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Export to CSV"):
            try:
                csv = export_df.to_csv(index=False)
                st.download_button(
                    "Download CSV",
                    csv,
                    "transactions.csv",
                    "text/csv",
                    key='download-csv'
                )
                st.success("CSV file ready for download!")
            except Exception as e:
                st.error(f"Error preparing CSV export: {str(e)}")
    
    with col2:
        if st.button("Export to Excel"):
            try:
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    export_df.to_excel(writer, index=False, sheet_name='Transactions')
                    
                    # Auto-adjust columns width
                    worksheet = writer.sheets['Transactions']
                    for idx, col in enumerate(export_df.columns):
                        max_length = max(
                            export_df[col].astype(str).apply(len).max(),
                            len(str(col))
                        )
                        worksheet.column_dimensions[chr(65 + idx)].width = max_length + 2
                
                buffer.seek(0)
                st.download_button(
                    "Download Excel",
                    buffer,
                    "transactions.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key='download-excel'
                )
                st.success("Excel file ready for download!")
            except Exception as e:
                st.error(f"Error preparing Excel export: {str(e)}")

else:
    st.info("No transactions found matching your search criteria.")