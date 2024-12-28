import streamlit as st
import sys
from pathlib import Path

# Add the root directory to Python path
root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

from database.db_manager import (
    init_settings_tables,
    get_setting,
    update_setting,
    get_category_thresholds,
    update_category_threshold,
    init_custom_categories,
    get_all_categories,
    add_custom_category,
    delete_custom_category
)

st.set_page_config(
    page_title="Settings - Money Manager",
    page_icon="⚙️",
    layout="wide"
)

st.title("Settings ⚙️")

# Initialize settings tables
init_settings_tables()

# Create tabs for different settings categories
tab1, tab2, tab3, tab4 = st.tabs(["Currency Settings", "Category Management", "Category Thresholds", "Notifications"])

# Currency Settings Tab
with tab1:
    st.subheader("Currency Settings")
    
    # Currency symbol
    currency_symbols = {
        "$": "US Dollar ($)",
        "€": "Euro (€)",
        "£": "British Pound (£)",
        "¥": "Japanese Yen (¥)",
        "₹": "Indian Rupee (₹)",
        "CHF": "Swiss Franc (CHF)",
        "A$": "Australian Dollar (A$)",
        "C$": "Canadian Dollar (C$)"
    }
    
    current_symbol = get_setting('currency_symbol') or '$'
    selected_symbol = st.selectbox(
        "Select Currency Symbol",
        options=list(currency_symbols.keys()),
        format_func=lambda x: currency_symbols[x],
        index=list(currency_symbols.keys()).index(current_symbol)
    )
    
    # Currency position
    current_position = get_setting('currency_position') or 'before'
    currency_position = st.radio(
        "Currency Symbol Position",
        options=['before', 'after'],
        format_func=lambda x: f"Before amount (e.g., {selected_symbol}100)" if x == 'before' else f"After amount (e.g., 100{selected_symbol})",
        index=0 if current_position == 'before' else 1
    )
    
    if st.button("Save Currency Settings", type="primary"):
        if update_setting('currency_symbol', selected_symbol) and \
           update_setting('currency_position', currency_position):
            st.success("Currency settings updated successfully!")
            st.rerun()

# Category Management Tab
with tab2:
    st.subheader("Category Management")
    
    # Initialize custom categories table
    init_custom_categories()
    
    # Get all categories
    all_categories = get_all_categories()
    
    # Add new category
    with st.form("add_category_form"):
        st.write("Add New Category")
        new_category = st.text_input(
            "Category Name",
            help="Enter the name of the new category"
        ).strip()
        
        submit_category = st.form_submit_button("Add Category", type="primary")
        
        if submit_category and new_category:
            if new_category in all_categories:
                st.error("This category already exists!")
            else:
                if add_custom_category(new_category):
                    st.success(f"Category '{new_category}' added successfully!")
                    st.rerun()
    
    # Display and manage existing categories
    st.write("### Existing Categories")
    st.write("Default categories cannot be deleted.")
    
    # Define default categories
    DEFAULT_CATEGORIES = {
        "Housing", "Transportation", "Groceries", "Food & Dining",
        "Shopping", "Entertainment", "Healthcare", "Education",
        "Utilities", "Insurance", "Savings", "Investments",
        "Income", "Other"
    }
    
    # Create three columns for better layout
    cols = st.columns(3)
    for i, category in enumerate(sorted(all_categories)):
        col_idx = i % 3
        with cols[col_idx]:
            if category in DEFAULT_CATEGORIES:
                st.info(f"📌 {category} (Default)")
            else:
                col1, col2 = st.columns([3, 1])
                col1.info(f"🏷️ {category}")
                if col2.button("🗑️", key=f"del_{category}", help=f"Delete {category}"):
                    if delete_custom_category(category):
                        st.success(f"Category '{category}' deleted successfully!")
                        st.rerun()

# Category Thresholds Tab
with tab3:
    st.subheader("Monthly Category Thresholds")
    st.info("""
    Set monthly spending limits for each category. You'll receive notifications when you approach or exceed these limits.
    Leave a threshold at 0 to disable monitoring for that category.
    """)
    
    # Get current thresholds
    thresholds_df = get_category_thresholds()
    current_thresholds = dict(zip(thresholds_df['category'], thresholds_df['monthly_limit']))
    
    # Get all categories (including custom ones)
    categories = get_all_categories()
    
    # Create a form for threshold settings
    with st.form("threshold_form"):
        # Create three columns for better layout
        cols = st.columns(3)
        thresholds = {}
        
        for i, category in enumerate(categories):
            if category != "Income":  # Skip Income category for thresholds
                col_idx = i % 3
                with cols[col_idx]:
                    thresholds[category] = st.number_input(
                        f"{category} Limit",
                        min_value=0.0,
                        value=float(current_thresholds.get(category, 0)),
                        step=50.0,
                        help=f"Set monthly spending limit for {category}"
                    )
        
        submitted = st.form_submit_button("Save Thresholds", type="primary", use_container_width=True)
        
        if submitted:
            success = True
            for category, limit in thresholds.items():
                if not update_category_threshold(category, limit):
                    success = False
                    break
            
            if success:
                st.success("Category thresholds updated successfully!")
                st.rerun()

# Notifications Tab
with tab4:
    st.subheader("Notification Settings")
    st.info("Configure how you want to be notified about your spending.")
    
    # Threshold Warning Level
    warning_level = st.slider(
        "Threshold Warning Level",
        min_value=50,
        max_value=100,
        value=80,
        step=5,
        help="Receive warnings when category spending reaches this percentage of the threshold"
    )
    
    # Notification Options
    st.write("Notification Options")
    show_warnings = st.checkbox(
        "Show warning messages when adding transactions",
        value=True,
        help="Display warnings when a transaction would exceed category thresholds"
    )
    
    show_dashboard = st.checkbox(
        "Show threshold status in dashboard",
        value=True,
        help="Display threshold status in the analytics dashboard"
    )
    
    if st.button("Save Notification Settings", type="primary"):
        if update_setting('warning_level', str(warning_level)) and \
           update_setting('show_warnings', str(show_warnings)) and \
           update_setting('show_dashboard', str(show_dashboard)):
            st.success("Notification settings updated successfully!")
            st.rerun()

# Add a section for data management
st.subheader("Data Management")
with st.expander("Export/Import Settings"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("Export Settings")
        if st.button("Download Settings as JSON"):
            # TODO: Implement settings export
            st.info("Feature coming soon!")
    
    with col2:
        st.write("Import Settings")
        settings_file = st.file_uploader("Upload Settings JSON")
        if settings_file is not None:
            # TODO: Implement settings import
            st.info("Feature coming soon!")